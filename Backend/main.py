import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

# Assuming 'agents' module is available in the environment or path
# If 'agents' is a custom module, ensure it's in the same directory or accessible via PYTHONPATH
try:
    from agents import Agent, Runner, trace, function_tool
except ImportError:
    print("Error: The 'agents' module was not found. Please ensure it's installed or in the Python path.")
    print("You might need to install it: pip install <your-agents-library>")
    # Exit or handle gracefully if 'agents' is critical and cannot be mocked
    exit(1)


# --- Load environment variables ---
load_dotenv(override=True)
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

if not RESEND_API_KEY:
    print("Warning: RESEND_API_KEY not found in environment variables. Email sending will fail.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="ComplAI Sales Email Sender",
    description="Backend for generating and sending sales emails using AI agents and Resend.",
    version="1.0.0"
)

# --- CORS Middleware Setup ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, consider restricting in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Allow specific methods
    allow_headers=["*"],  # Allow all headers
)

# --- Pydantic Model for Request Body ---
class EmailRequest(BaseModel):
    user_query: str = "Write a cold sales email about ComplAI's SOC2 compliance tool."
    to_email_address: str = "tuemail@gmail.com"
    subject: str = "Consulta sobre cumplimiento SOC2 con ComplAI"


# --- Function to send emails, decorated as a tool ---
@function_tool
def send_email(body: str, subject: str = "Email de ventas", to_email_address: str = "tuemail@gmail.com"):
    """
    Sends an email using the Resend API.
    This function is exposed as a tool for the AI agents.
    """
    if not RESEND_API_KEY:
        print("RESEND_API_KEY is not set. Cannot send email.")
        return {"status": "failure", "message": "RESEND_API_KEY not configured."}

    # Ensure this email address is verified in your Resend account
    from_email = "info@mamaencalma.com" # Replace with your verified Resend email

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "from": f"Testing antoniet <{from_email}>",
        "to": [to_email_address],
        "subject": subject,
        "html": f"<p>{body}</p>"
    }

    try:
        print(f"Attempting to send email to {to_email_address} with subject: {subject}")
        response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        response_data = response.json()
        if response.status_code == 202:
            print(f"✅ Email sent successfully to {to_email_address}. ID: {response_data.get('id')}")
            return {"status": "success", "id": response_data.get('id'), "message": "Email sent successfully!"}
        else:
            print(f"⚠️ Email processed with non-202 code: {response.status_code}, {response.text}")
            return {"status": "info", "message": response.text}
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending email: {e}")
        return {"status": "failure", "message": str(e)}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"status": "failure", "message": str(e)}

# --- Core Business Logic: Email Generation and Sending ---
async def generate_and_send_email_workflow(
    user_query: str, to_email_address: str, subject: str
):
    """
    Encapsulates the AI agent workflow for generating and sending a sales email.
    Collects and returns detailed steps of the process.
    """
    steps_log = []

    instructions_base = "a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI."

    # Instructions for each agent
    instructions1 = f"You are a sales agent working for ComplAI, {instructions_base} You write professional, serious cold emails."
    instructions2 = f"You are a humorous, engaging sales agent working for ComplAI, {instructions_base} You write witty, engaging cold emails that are likely to get a response."
    instructions3 = f"You are a busy sales agent working for ComplAI, {instructions_base} You write concise, to the point cold emails."

    # Create writing agents
    sales_agent1 = Agent(name="Professional Sales Agent", instructions=instructions1, model="gpt-4o-mini")
    sales_agent2 = Agent(name="Engaging Sales Agent", instructions=instructions2, model="gpt-4o-mini")
    sales_agent3 = Agent(name="Busy Sales Agent", instructions=instructions3, model="gpt-4o-mini")

    # Picker to choose the best email
    sales_picker = Agent(
        name="sales_picker",
        instructions="You pick the best cold sales email from the given options. "
                     "Imagine you are a customer and pick the one you are most likely to respond to. "
                     "Do not give an explanation; reply with the selected email only.",
        model="gpt-4o-mini"
    )

    # Convert agents into tools
    description_email_tool = "Write a cold sales email"
    tool1 = sales_agent1.as_tool(tool_name="sales_agent1_tool", tool_description=description_email_tool)
    tool2 = sales_agent2.as_tool(tool_name="sales_agent2_tool", tool_description=description_email_tool)
    tool3 = sales_agent3.as_tool(tool_name="sales_agent3_tool", tool_description=description_email_tool)

    # Sales Manager with tools
    instructions_manager = (
        "You are a sales manager working for ComplAI. You use the tools given to you to generate cold sales emails. "
        "You never generate sales emails yourself; you always use the tools. "
        "You try all 3 sales_agent tools once before choosing the best one. "
        "You pick the single best email and use the send_email tool to send the best email (and only the best email) to the user."
    )
    tools_for_manager = [tool1, tool2, tool3, send_email]

    sales_manager = Agent(
        name="Sales Manager",
        instructions=instructions_manager,
        tools=tools_for_manager,
        model="gpt-4o-mini"
    )

    # --- Phase 1: Generate emails ---
    steps_log.append({"step": "Inicio del proceso", "message": "Generando emails con los agentes de ventas..."})
    print("\n--- Generating emails with sales agents ---")
    with trace("Sales Email Generation"):
        results = await asyncio.gather(
            Runner.run(sales_agent1, user_query),
            Runner.run(sales_agent2, user_query),
            Runner.run(sales_agent3, user_query),
        )
        outputs = [result.final_output for result in results]

        emails_for_picker = "Cold sales emails:\n\n" + "\n\n---\n\n".join(outputs)

        steps_log.append({"step": "Generación de Emails", "message": "Tres borradores de email generados.", "details": outputs})
        print("\n--- Generated Emails ---")
        for i, email in enumerate(outputs):
            print(f"\nEmail {i + 1}:\n{email}")
            print("-" * 40)

        # --- Phase 2: Select the best email ---
        steps_log.append({"step": "Selección del Mejor Email", "message": "El agente selector está eligiendo el mejor email..."})
        print("\n--- Selecting the best email ---")
        best_email_result = await Runner.run(sales_picker, emails_for_picker)
        best_email_content = best_email_result.final_output

        steps_log.append({"step": "Email Seleccionado", "message": "El mejor email ha sido seleccionado.", "details": best_email_content})
        print(f"\n✅ Best email selected:\n{best_email_content}")

    # --- Phase 3: Sales Manager sends the best email ---
    steps_log.append({"step": "Envío de Email", "message": f"El Sales Manager está enviando el email a {to_email_address}..."})
    print("\n--- Sales Manager will send the best email ---")
    manager_message = (
        "Please use the 'send_email' tool to send the following email:\n\n"
        f"body: {best_email_content}\n"
        f"subject: {subject}\n"
        f"to_email_address: {to_email_address}"
    )

    with trace("Sales Manager in action"):
        manager_run_result = await Runner.run(sales_manager, manager_message)
        final_output = manager_run_result.final_output
        steps_log.append({"step": "Email Enviado", "message": "Proceso completado.", "details": final_output})
        print(f"\n📤 Final result from Sales Manager:\n{final_output}")
        return {"status": "success", "steps": steps_log, "final_email_sent_result": final_output}


# --- FastAPI Endpoint ---
@app.post("/send-sales-email/")
async def send_sales_email_endpoint(request: EmailRequest):
    """
    Endpoint to trigger the sales email generation and sending workflow.
    Expects a JSON body with 'user_query', 'to_email_address', and 'subject'.
    Returns detailed steps and final result.
    """
    try:
        print(f"Received request to send email: {request.dict()}")
        result = await generate_and_send_email_workflow(
            request.user_query,
            request.to_email_address,
            request.subject
        )
        return {"message": "Email workflow initiated successfully", "data": result}
    except Exception as e:
        print(f"Error in /send-sales-email/ endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# --- Health Check Endpoint ---
@app.get("/")
async def read_root():
    """Basic health check endpoint."""
    return {"message": "ComplAI Sales Email Sender Backend is running!"}
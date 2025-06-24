import { useState } from "react";
import axios from "axios";
import "./App.css"; // We'll create this file for styling

interface Step {
  step: string;
  message: string;
  details?: any; // To hold generated emails or final send result
}

function App() {
  const [userQuery, setUserQuery] = useState(
    "Write a cold sales email about ComplAI's SOC2 compliance tool."
  );
  const [subject, setSubject] = useState(
    "Consulta sobre cumplimiento SOC2 con ComplAI"
  );
  const [toEmail, setToEmail] = useState("tuemail@gmail.com");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progressSteps, setProgressSteps] = useState<Step[]>([]);
  const [finalEmailContent, setFinalEmailContent] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);
    setError(null);
    setProgressSteps([]); // Clear previous steps
    setFinalEmailContent(null);

    try {
      const res = await axios.post("http://localhost:8000/send-sales-email/", {
        user_query: userQuery,
        to_email_address: toEmail,
        subject: subject,
      });

      const { data } = res.data; // Access the 'data' field from the FastAPI response
      if (data && data.steps) {
        setProgressSteps(data.steps);
        // Find the "Email Seleccionado" step to display the best email
        const selectedEmailStep = data.steps.find((step: Step) => step.step === "Email Seleccionado");
        if (selectedEmailStep && selectedEmailStep.details) {
          setFinalEmailContent(selectedEmailStep.details);
        }
        setResponse("✅ Workflow de email completado con éxito.");
      } else {
        setResponse(data.final_email_sent_result?.message || "✅ Email enviado correctamente.");
      }
    } catch (err: any) {
      setError("❌ Error al enviar el email: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>ComplAI Sales Email Sender</h1>
        <p className="subtitle">Genera y envía emails de ventas asistidos por IA para SOC2.</p>
      </header>

      <form onSubmit={handleSubmit} className="form-card">
        <div className="form-group">
          <label htmlFor="toEmail">Para:</label>
          <input
            id="toEmail"
            type="email"
            value={toEmail}
            onChange={(e) => setToEmail(e.target.value)}
            required
            className="input-field"
          />
        </div>
        <div className="form-group">
          <label htmlFor="subject">Asunto:</label>
          <input
            id="subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
            className="input-field"
          />
        </div>
        <div className="form-group">
          <label htmlFor="userQuery">Consulta de Usuario:</label>
          <textarea
            id="userQuery"
            value={userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
            rows={6}
            className="textarea-field"
          />
        </div>
        <button type="submit" disabled={loading} className="submit-button">
          {loading ? "Enviando..." : "Enviar Email"}
        </button>
      </form>

      {loading && (
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Procesando solicitud...</p>
        </div>
      )}

      {progressSteps.length > 0 && (
        <div className="status-card">
          <h3>Estado del Proceso:</h3>
          <ul className="progress-list">
            {progressSteps.map((step, index) => (
              <li key={index} className="progress-item">
                <strong>{step.step}:</strong> {step.message}
                {step.step === "Generación de Emails" && step.details && (
                  <div className="generated-emails">
                    {step.details.map((email: string, emailIndex: number) => (
                      <div key={emailIndex} className="email-preview">
                        <h4>Email Borrador {emailIndex + 1}</h4>
                        <pre>{email}</pre>
                      </div>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {finalEmailContent && (
        <div className="result-card">
          <h3>📧 Mejor Email Seleccionado:</h3>
          <pre className="final-email-display">{finalEmailContent}</pre>
        </div>
      )}

      {response && !loading && (
        <div className="result-card success">
          <h3>✅ Éxito:</h3>
          <p>{response}</p>
        </div>
      )}

      {error && (
        <div className="result-card error">
          <h3>❌ Error:</h3>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}

export default App;
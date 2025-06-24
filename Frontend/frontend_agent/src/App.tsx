import { useState } from "react";
import axios from "axios";

function App() {
  const [userQuery, setUserQuery] = useState(
    "Write a cold sales email about ComplAI's SOC2 compliance tool."
  );
  const [subject, setSubject] = useState(
    "Consulta sobre cumplimiento SOC2 con ComplAI"
  );
  const [toEmail, setToEmail] = useState("empresaliax@gmail.com");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);
    setError(null);

    try {
      const res = await axios.post("http://localhost:8000/send-sales-email/", {
        user_query: userQuery,
        to_email_address: toEmail,
        subject: subject,
      });

      setResponse(res.data.details ?? "✅ Email enviado correctamente.");
    } catch (err: any) {
      setError("❌ Error al enviar el email: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: "2rem", fontFamily: "Arial, sans-serif" }}>
      <h1>ComplAI Sales Email Sender</h1>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem", maxWidth: 600 }}>
        <label>
          To Email Address:
          <input
            type="email"
            value={toEmail}
            onChange={(e) => setToEmail(e.target.value)}
            required
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </label>

        <label>
          Subject:
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </label>

        <label>
          User Query:
          <textarea
            value={userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
            rows={6}
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </label>

        <button type="submit" disabled={loading} style={{ padding: "0.75rem", background: "#2c7", color: "#fff", border: "none", cursor: "pointer" }}>
          {loading ? "Enviando..." : "Enviar Email"}
        </button>
      </form>

      {response && (
        <div style={{ marginTop: "2rem", background: "#eef", padding: "1rem", borderRadius: "0.5rem" }}>
          <h3>✅ Respuesta:</h3>
          <pre>{response}</pre>
        </div>
      )}

      {error && (
        <div style={{ marginTop: "2rem", background: "#fdd", padding: "1rem", borderRadius: "0.5rem", color: "#900" }}>
          <h3>❌ Error:</h3>
          <pre>{error}</pre>
        </div>
      )}
    </main>
  );
}

export default App;

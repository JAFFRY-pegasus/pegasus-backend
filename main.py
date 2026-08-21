<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PEGASUS IA - Pronostics SGE</title>
  <style>
    :root {
      --bg-color: #0f172a;
      --card-bg: #1e293b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-green: #10b981;
      --accent-blue: #3b82f6;
      --accent-blue-hover: #2563eb;
      --border-color: #334155;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-main);
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      padding: 20px;
      box-sizing: border-box;
    }

    .card {
      background-color: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 28px;
      width: 100%;
      max-width: 480px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
    }

    .header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }

    .title-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }

    .badge {
      background-color: var(--accent-blue);
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 12px;
      text-transform: uppercase;
    }

    /* Voyant vert clignotant */
    .dot-green {
      width: 12px;
      height: 12px;
      background-color: #2ecc71;
      border-radius: 50%;
      display: inline-block;
      box-shadow: 0 0 10px #2ecc71;
      animation: clignoter 1.5s infinite ease-in-out;
    }

    @keyframes clignoter {
      0% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.25; transform: scale(0.85); }
      100% { opacity: 1; transform: scale(1); }
    }

    .subtitle {
      color: var(--text-muted);
      font-size: 14px;
      margin-top: 0;
      margin-bottom: 24px;
    }

    .info-box {
      background-color: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 14px 18px;
      margin-bottom: 24px;
    }

    .info-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 0;
      font-size: 15px;
    }

    .info-row:not(:last-child) {
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .info-row span {
      color: var(--text-muted);
    }

    .info-row strong {
      color: var(--text-main);
      font-weight: 700;
    }

    .selection-box {
      background-color: #065f46;
      border: 1px solid #047857;
      border-radius: 12px;
      padding: 20px;
      text-align: center;
      margin-bottom: 24px;
    }

    .selection-box h3 {
      margin: 0 0 12px 0;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #a7f3d0;
      font-weight: 700;
    }

    .numbers {
      font-size: 26px;
      font-weight: 900;
      letter-spacing: 2px;
      color: #ffffff;
      text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    button {
      width: 100%;
      background-color: var(--accent-blue);
      color: #ffffff;
      border: none;
      border-radius: 10px;
      padding: 14px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      transition: background-color 0.2s ease, transform 0.1s ease;
    }

    button:hover {
      background-color: var(--accent-blue-hover);
    }

    button:active {
      transform: scale(0.99);
    }

    .status-footer {
      text-align: center;
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 16px;
      margin-bottom: 0;
    }
  </style>
</head>
<body>

  <div class="card">
    <!-- En-tête avec titre et signal clignotant -->
    <div class="header-row">
      <div class="title-group">
        <h1>PEGASUS IA</h1>
        <span class="badge">SGE v6.0</span>
      </div>
      <div class="status-indicator">
        <span class="dot-green" title="Service actif"></span>
      </div>
    </div>

    <p class="subtitle">Analyse géométrique & résonances matinales</p>

    <!-- Bloc d'information -->
    <div class="info-box">
      <div class="info-row">
        <span>Favori de la presse :</span>
        <strong id="favori-val">Chargement...</strong>
      </div>
      <div class="info-row">
        <span>Non partant(s) :</span>
        <strong id="np-val">Chargement...</strong>
      </div>
    </div>

    <!-- Pronostic -->
    <div class="selection-box">
      <h3>MON PRONOSTIC PEGASUS IA !</h3>
      <div id="quinte-display" class="numbers">-- - -- - -- - -- - --</div>
    </div>

    <!-- Bouton d'action -->
    <button id="btn-refresh" onclick="chargerPronostic()">Actualisation</button>

    <p id="status-msg" class="status-footer">Dernière mise à jour effectuée avec succès.</p>
  </div>

  <script>
    const API_URL = "https://pegasus-backend-c3a6.onrender.com/predict";

    async function chargerPronostic() {
      const btn = document.getElementById("btn-refresh");
      const favoriEl = document.getElementById("favori-val");
      const npEl = document.getElementById("np-val");
      const quinteEl = document.getElementById("quinte-display");
      const statusEl = document.getElementById("status-msg");

      btn.disabled = true;
      btn.innerText = "Calcul en cours...";
      statusEl.innerText = "Connexion au serveur PEGASUS...";

      try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("Erreur serveur");
        
        const data = await response.json();

        // Mise à jour de l'affichage
        favoriEl.innerText = "Cheval " + data.favori;
        
        if (data.non_partants && data.non_partants.length > 0) {
          npEl.innerText = data.non_partants.join(", ");
        } else {
          npEl.innerText = "Aucun";
        }

        quinteEl.innerText = data.quinte_sge.join(" - ");
        statusEl.innerText = "Dernière mise à jour effectuée avec succès.";

      } catch (error) {
        console.error("Erreur :", error);
        statusEl.innerText = "Erreur de connexion avec le serveur.";
      } finally {
        btn.disabled = false;
        btn.innerText = "Actualisation";
      }
    }

    // Chargement automatique au lancement de la page
    window.onload = chargerPronostic;
  </script>

</body>
</html>

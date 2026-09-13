document.addEventListener("DOMContentLoaded", async () => {
  const sessionBadge = document.getElementById("session-badge");
  const accessBadge = document.getElementById("access-badge");
  const userDisplay = document.getElementById("user-display");
  const btnExport = document.getElementById("btn-export");
  const btnCopy = document.getElementById("btn-copy");

  let sessionToken = null;
  let accessToken = null;
  let userEmail = null;

  try {
    const cookies = await chrome.cookies.getAll({ domain: "chatgpt.com" });
    const sessionCookie = cookies.find(c => c.name === "__Secure-next-auth.session-token");

    if (sessionCookie && sessionCookie.value) {
      sessionToken = sessionCookie.value;
      sessionBadge.textContent = "Present";
      sessionBadge.className = "status-badge badge-ok";

      // Fetch active access token from session endpoint
      try {
        const resp = await fetch("https://chatgpt.com/api/auth/session");
        if (resp.ok) {
          const data = await resp.json();
          if (data.accessToken) {
            accessToken = data.accessToken;
            accessBadge.textContent = "Valid";
            accessBadge.className = "status-badge badge-ok";
          }
          if (data.user && data.user.email) {
            userEmail = data.user.email;
            userDisplay.textContent = userEmail;
          }
        }
      } catch (e) {
        console.error("Failed to fetch session:", e);
      }
    } else {
      sessionBadge.textContent = "Not Logged In";
      sessionBadge.className = "status-badge badge-missing";
    }

    if (sessionToken || accessToken) {
      btnExport.disabled = false;
      if (accessToken) btnCopy.disabled = false;
    }
  } catch (err) {
    console.error("Cookie error:", err);
    sessionBadge.textContent = "Error";
  }

  btnExport.addEventListener("click", () => {
    const exportData = {
      session_token: sessionToken,
      access_token: accessToken,
      email: userEmail,
      exported_at: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "chatgpt-auth.json";
    a.click();
    URL.revokeObjectURL(url);
  });

  btnCopy.addEventListener("click", async () => {
    if (accessToken) {
      await navigator.clipboard.writeText(accessToken);
      btnCopy.textContent = "Copied to Clipboard!";
      setTimeout(() => { btnCopy.textContent = "Copy Access Token"; }, 2000);
    }
  });
});

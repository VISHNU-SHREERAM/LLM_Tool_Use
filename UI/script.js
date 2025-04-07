document.addEventListener("DOMContentLoaded", () => {
  // --- Get DOM Elements ---
  const chatMessages = document.getElementById("chat-messages");
  const userInput = document.getElementById("user-input");
  const sendButton = document.getElementById("send-button");

  // --- API Configuration ---
  // IMPORTANT: Use http:// for localhost unless you have explicitly set up HTTPS.
  // Update port if your backend runs elsewhere.
  const apiUrl = "http://localhost:8000/ask";

  // --- Function to add a message to the chat window ---
  function addMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add(
      "message",
      sender === "user" ? "user-message" : "bot-message"
    );

    // --- Markdown Processing ---
    let processedText = text;

    // 1. Images: ![alt text](url) -> <img src="url" alt="alt text">
    // Added style for responsiveness, display block, margin, and rounding
    processedText = processedText.replace(
      /!\[(.*?)\]\((.*?)\)/g, // Regex: ![alt](url)
      (match, alt, url) => {
        // Basic check for potentially harmful protocols (allow http, https, data)
        if (
          url.startsWith("http://") ||
          url.startsWith("https://") ||
          url.startsWith("data:")
        ) {
          // Sanitize alt text slightly by escaping HTML entities
          const sanitizedAlt = alt
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
          return `<img src="${url}" alt="${sanitizedAlt}" style="max-width: 100%; height: auto; display: block; margin-top: 5px; border-radius: 5px; background-color: #eee;">`; // Added background color while loading
        } else {
          console.warn(`Blocked image URL with invalid protocol: ${url}`);
          return `[Image blocked: Invalid URL protocol]`; // Handle potentially unsafe URLs
        }
      }
    );

    // 2. Links: [link text](url) -> <a href="url">link text</a>
    // Added target="_blank" for opening in new tab and rel for security
    processedText = processedText.replace(
      /\[(.*?)\]\((.*?)\)/g, // Regex: [text](url)
      (match, linkText, url) => {
        // Basic check for potentially harmful protocols (allow http, https)
        if (url.startsWith("http://") || url.startsWith("https://")) {
          // Sanitize link text slightly
          const sanitizedText = linkText
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
          return `<a href="${url}" target="_blank" rel="noopener noreferrer">${sanitizedText}</a>`;
        } else {
          console.warn(`Blocked link URL with invalid protocol: ${url}`);
          return `[Link blocked: Invalid URL protocol]`; // Handle potentially unsafe URLs
        }
      }
    );

    // 3. Bold: **text** -> <strong>text</strong>
    // This should come AFTER image/link processing to avoid conflicts
    processedText = processedText.replace(
      /\*\*(.*?)\*\*/g,
      "<strong>$1</strong>"
    );

    // --- End Markdown Processing ---

    // Use innerHTML to render the generated HTML tags (<img>, <a>, <strong>).
    // WARNING: This assumes the LLM output is generally trustworthy and doesn't
    //          contain intentionally malicious script tags within the markdown.
    //          The basic URL protocol checks add a minimal safety layer.
    messageDiv.innerHTML = processedText;

    chatMessages.appendChild(messageDiv);

    // Scroll to the bottom to show the latest message
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // --- Function to send message to API and handle response ---
  async function sendMessageToLLM() {
    const promptText = userInput.value.trim();
    if (!promptText) return; // Don't send empty messages

    // Display user's message immediately
    addMessage(promptText, "user");
    userInput.value = ""; // Clear input field
    userInput.focus(); // Keep focus on input

    // --- Add Typing Indicator ---
    const typingIndicator = document.createElement("div");
    typingIndicator.classList.add("message", "bot-message");
    typingIndicator.innerHTML = "<p><i>🥹 Helping You. Please Wait...</i></p>";
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll down to show indicator

    try {
      // --- Call the API ---
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Add any other headers like 'Accept: application/json' or Authorization if needed
          Accept: "application/json",
        },
        body: JSON.stringify({ prompt: promptText }), // Send prompt in correct format
      });

      // --- Remove Typing Indicator ---
      chatMessages.removeChild(typingIndicator);

      // --- Handle API Response ---
      if (!response.ok) {
        // Handle HTTP errors (e.g., 404 Not Found, 500 Internal Server Error)
        const errorText = `Error: ${response.status} ${response.statusText}`;
        console.error("API Error:", errorText);
        // Try to get error message from response body if available
        let serverErrorMsg = "";
        try {
          const errorData = await response.json();
          serverErrorMsg =
            errorData.detail || errorData.message || JSON.stringify(errorData);
        } catch (e) {
          // Ignore if response body isn't JSON or empty
        }
        addMessage(
          `Sorry, I encountered an error trying to reach the server. (${
            response.status
          })${serverErrorMsg ? ": " + serverErrorMsg : ""}`,
          "bot"
        );
        return;
      }

      // --- Process Successful Response ---
      const data = await response.json();

      // Check if the expected 'result' field exists
      if (data && data.result !== undefined) {
        // Check for undefined specifically, as result could be empty string
        addMessage(data.result, "bot"); // Display the bot's message
      } else {
        console.error("API Response format incorrect:", data);
        addMessage(
          "Sorry, I received an unexpected response format from the server.",
          "bot"
        );
      }
    } catch (error) {
      // --- Handle Network or other errors ---
      console.error("Network or Fetch Error:", error);

      // --- Remove Typing Indicator (if it wasn't removed already) ---
      // Check if it still exists before trying to remove
      const stillTyping = chatMessages.querySelector(".message > p > i"); // More specific selector
      if (
        stillTyping &&
        stillTyping.textContent === "Typing..." &&
        stillTyping.closest(".bot-message")
      ) {
        chatMessages.removeChild(stillTyping.closest(".bot-message"));
      }

      addMessage(
        `Sorry, I couldn't connect to the chat service. Please check your network connection or if the server is running. Error: ${error.message}`,
        "bot"
      );
    }
  }

  // --- Event Listeners ---

  // Send button click
  sendButton.addEventListener("click", sendMessageToLLM);

  // Enter key press in input field
  userInput.addEventListener("keydown", (event) => {
    // Send message on Enter key press
    if (event.key === "Enter") {
      event.preventDefault(); // Prevent default behavior (like form submission if it was in one)
      sendMessageToLLM();
    }
  });

  // Optional: Add a welcome message when the chat loads
  addMessage("Hello! How can I assist you today?", "bot");
  // Note: The initial message is currently hardcoded in index.html, which is simpler.
}); // End DOMContentLoaded

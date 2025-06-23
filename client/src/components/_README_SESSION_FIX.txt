// Patch for fetch to always send credentials (cookies) with requests
// Place this at the top of your main entry file or before any fetch calls if needed

// If you use fetch directly in your code, you must add credentials: 'include' to each call.
// Here is a patch for your CHATUI.jsx usage:

// In CHATUI.jsx, update the fetch call in sendMessage:
//
// const response = await fetch('https://rag-narok-ul49.onrender.com/chat', {
//   method: 'POST',
//   headers: {
//     'Content-Type': 'application/json',
//   },
//   body: JSON.stringify({ query: input }),
//   credentials: 'include', // <-- ADD THIS LINE
// });

// This ensures cookies (including Flask session) are sent and received.

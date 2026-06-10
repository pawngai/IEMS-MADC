import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import ErrorBoundary from "@/app/layout/ErrorBoundary";

// Suppress benign ResizeObserver loop warnings (common with Radix UI / dynamic layouts).
// Must run in capture phase to intercept before React dev overlay's handleError.
const resizeObserverMsg = /ResizeObserver loop/;
if (typeof window !== "undefined") {
  // Capture-phase error listener - fires before React's dev overlay handler
  window.addEventListener(
    "error",
    (e) => {
      if (e.message && resizeObserverMsg.test(e.message)) {
        e.stopImmediatePropagation();
        e.stopPropagation();
        e.preventDefault();
      }
    },
    true
  );

  // Also suppress if surfaced as an unhandled rejection
  window.addEventListener("unhandledrejection", (e) => {
    if (e.reason && resizeObserverMsg.test(String(e.reason))) {
      e.preventDefault();
    }
  });
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  React.createElement(
    React.StrictMode,
    null,
    React.createElement(
      ErrorBoundary,
      null,
      React.createElement(App, null)
    )
  )
);

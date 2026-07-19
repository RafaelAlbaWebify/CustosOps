import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";
import "./guiRuntimeFixes";
import "./mock-dashboard-refresh.css";
import "./overview-responsive.css";
import "./trace-visual-foundation.css";
import "./trace-navigation-polish.css";
import "./trace-workspace-refinement.css";
import "./trace-light-card-cleanup.css";
import "./gui-regression-fixes.css";
import "./overview-window-layout-fixes.css";
import "./final-overview-polish.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import "./index.css";
import "./i18n";

import App from "./App";
import SetupPage from "./pages/SetupPage";
import CreatorPage from "./pages/CreatorPage";
import AnalysisPage from "./pages/AnalysisPage";
import ReportPage from "./pages/ReportPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <SetupPage /> },
      { path: "creator", element: <CreatorPage /> },
      { path: "analysis/:runId", element: <AnalysisPage /> },
      { path: "report/:runId", element: <ReportPage /> },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);

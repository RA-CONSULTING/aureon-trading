import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { initNetworkMonitoring } from "./core/networkMonitor";

// Initialize network monitoring before app renders
initNetworkMonitoring();

createRoot(document.getElementById("root")!).render(<App />);

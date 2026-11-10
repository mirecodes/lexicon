import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App.tsx";
import { getTheme, setTheme, syncBar } from "./lexicon.ts";
import "./styles.css";

setTheme(getTheme());
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", syncBar);

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);

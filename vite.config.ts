import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// relative base: works at mirecodes.github.io/lexicon/ and on localhost alike (routing is hash-based)
export default defineConfig({ base: "./", plugins: [react()] });

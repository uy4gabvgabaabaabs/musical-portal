import { cp, mkdir } from "node:fs/promises";
import path from "node:path";

const source = path.resolve("exports");
const destination = path.resolve("public", "downloads");

await mkdir(destination, { recursive: true });
await cp(source, destination, { recursive: true, force: true });


/**
 * Server-side proxy to the FastAPI backend. The operator token is injected
 * HERE, on the Next server, so it never ships to the browser (spec: "never
 * expose secrets or API keys client-side"). The browser only ever calls
 * /api/proxy/...; the token lives in GEOAR_OPERATOR_TOKEN on the web server.
 */
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.GEOAR_API_URL ?? "http://localhost:8000";
// Dev default matches the backend's dev default; set both env vars in any real deployment.
const TOKEN = process.env.GEOAR_OPERATOR_TOKEN ?? "geoar-dev-operator";

async function forward(req: NextRequest, path: string[]) {
  const search = req.nextUrl.search;
  const upstream = `${API_URL}/api/${path.join("/")}${search}`;

  const headers: Record<string, string> = { "X-Operator-Token": TOKEN };
  const contentType = req.headers.get("content-type");
  if (contentType) headers["content-type"] = contentType;

  const res = await fetch(upstream, {
    method: req.method,
    headers,
    body: req.method === "GET" || req.method === "HEAD" ? undefined : req.body,
    // @ts-expect-error duplex is required by Node fetch for streaming bodies
    duplex: "half",
    cache: "no-store",
  });

  return new NextResponse(res.body, {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") ?? "application/json" },
  });
}

type Ctx = { params: { path: string[] } };
export async function GET(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
export async function POST(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
export async function PUT(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}

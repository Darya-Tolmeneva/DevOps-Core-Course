export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    console.log("request v2 v2", {
      path: url.pathname,
      method: request.method,
      colo: request.cf?.colo,
      country: request.cf?.country,
    });

    // GET /
    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    // GET /health
    if (url.pathname === "/health") {
      return Response.json(
        {
          status: "ok",
          uptime: "running",
        },
        {
          status: 200,
        }
      );
    }

    // GET /edge
    if (url.pathname === "/edge") {
      return Response.json({
        colo: request.cf?.colo,
        country: request.cf?.country,
        city: request.cf?.city,
        asn: request.cf?.asn,
        httpProtocol: request.cf?.httpProtocol,
        tlsVersion: request.cf?.tlsVersion,
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/config") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
      });
    }

    if (url.pathname === "/secrets") {
      return Response.json({
        token: env.API_TOKEN,
        admin: env.ADMIN_EMAIL,
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");

      const visits = Number(raw ?? "0") + 1;

      await env.SETTINGS.put("visits", String(visits));

      return Response.json({
        visits,
      });
    }

    // 404
    return Response.json(
      {
        error: "Not Found",
      },
      {
        status: 404,
      }
    );
  },
};

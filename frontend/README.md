This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Static export (SSG)

If you want to produce a static (SSG) export of the frontend and avoid running it as a container/server, use the provided build script which runs a Next.js build and `next export` to `frontend/out`:

From the repository root:

```fish
# build and export the static site
./scripts/build_frontend.sh
# or (if not executable)
sh ./scripts/build_frontend.sh
```

Serve the exported static files (examples):

```fish
# using a small Node static server (recommended for correct MIME handling)
npx serve -s frontend/out -l 3000

# or with Python's builtin server
python3 -m http.server 3000 --directory frontend/out
```

Notes & compatibility

- `next export` (used by `next export` and therefore this script) only supports pages that can be fully statically exported. Pages that rely on server-side rendering (e.g. `getServerSideProps`) or certain App Router server-only features may not be exportable.

- This repository uses the App Router (the `src/app` directory). The App Router and Next.js server components can include server-only behavior (server actions, dynamic rendering, incremental/on-demand revalidation, PPR). Those features may make a full static export impossible.

- If `./scripts/build_frontend.sh` fails with messages about server-only APIs or `next export` not being supported, you have three main options:
  1. Keep the frontend as a server (run `next start` or use the previously defined Docker container).
  2. Convert affected pages/routes to static-friendly APIs (use static data fetching or pre-generate via `getStaticProps` / static params where appropriate).
  3. Deploy to a platform that supports Next.js server runtime (Vercel, or host `next start` in a container).

- I checked for obvious `getServerSideProps` usage under `frontend/src` and didn't find it, but App Router server features can still block export. If you want, I can try running the export locally and report exact errors.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

# alexandercaldwell.com

Source for [alexandercaldwell.com](https://alexandercaldwell.com), a static site deployed on [Vercel](https://vercel.com).

No build step, no dependencies: plain HTML and CSS.

## Files

```
index.html        # home page (about, work, contact sections)
404.html          # not-found page
assets/style.css  # styles (light/dark via CSS variables)
assets/favicon.svg
robots.txt
sitemap.xml
vercel.json       # clean URLs, security and cache headers
```

## Editing

Edit `index.html` directly. Text, links and the email address live in that file; colours and
spacing live in `assets/style.css`.

## Local preview

Open `index.html` in a browser, or serve the folder:

```bash
npx serve .
```

## Deploying

The repository is linked to Vercel. Every push to `main` deploys to production; other branches
get preview URLs. The custom domain is configured under **Project → Settings → Domains** in Vercel.

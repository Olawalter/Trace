# Fonts, kept here on purpose

These three files are the latin subsets of Instrument Serif, Schibsted Grotesk
and Azeret Mono, served from this repository rather than fetched while the site
is built.

`next/font/google` is the obvious way to use them and it was how this console
started. It downloads the files during `next build`, which quietly makes every
build depend on `fonts.gstatic.com` being reachable at that moment. That is a
third-party service standing between a clean checkout and a working build, and
it broke CI once on a commit that changed nothing but three markdown files.

A repository whose entire argument is that you should be able to check things
for yourself should not need somebody else's CDN to compile. So the files live
here, `next/font/local` reads them off disk, and `npm run build` needs nothing
but this checkout.

| File | Family | Axes |
| --- | --- | --- |
| `instrument-serif-400.woff2` | Instrument Serif | 400 only, which is the whole point of it here |
| `schibsted-grotesk-variable.woff2` | Schibsted Grotesk | variable, 400 to 800 |
| `azeret-mono-variable.woff2` | Azeret Mono | variable, 400 to 500 |

All three are published under the SIL Open Font License 1.1, which permits
redistributing the files inside a larger work like this one. See `OFL.txt` for
the licence text and the reserved font names it applies to.

To refresh them, take the `U+0000-00FF` block from each family's
`fonts.googleapis.com/css2` response and download the `woff2` it names.

# RDN-website

https://responsediversitynetwork.github.io/RDN-website/

## How to contribute to this website

If you have an idea to improve the website, please let us know about it! You could do so using the form on the ["Join" page](https://responsediversitynetwork.github.io/RDN-website/join.html) to let us know. Or you could create an issue in this repository (you will have to be logged in to github).

Once we see that your idea is a good one, you could implement it yourself if you're familiar with making websites with [quarto](https://quarto.org/docs/websites/) and with using git/github. In that case, please fork the repo, make the changes in your fork, and create a pull request. Otherwise one of the existing contributors will implement the idea.

The website is published from the "live" branch.

## Updating the map

The interactive map is made here: https://github.com/ResponseDiversityNetwork/RDN_member_map 

## Project register (Resources → Projects)

The pages under `projectbase/` are not stored in this repository. They are copied from [rdn-projectbase](https://github.com/ResponseDiversityNetwork/rdn-projectbase), which still handles form submissions, pull requests and its own site.

`scripts/sync_projectbase.py` runs automatically before every `quarto render` (`pre-render` in `_quarto.yml`). It reuses `rdn-projectbase/scripts/build_site.py` to validate the project files and generate one page per project. It needs Python 3 with `pyyaml` and `jsonschema` (`pip install pyyaml "jsonschema[format]"`).

It takes the register from, in order: the folder in the environment variable `RDN_PROJECTBASE_DIR`; a sibling folder `../rdn-projectbase`; or a fresh clone from GitHub (always the case on GitHub Actions). When rendering locally from the sibling folder, `git pull` it first to see the latest projects.

The website rebuilds when rdn-projectbase publishes (it sends a `projectbase-updated` dispatch; see `docs/SETUP.md` there), once a day as a fallback, and on demand from the Actions tab (*Quarto Publish → Run workflow*).

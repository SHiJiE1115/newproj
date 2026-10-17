V21 authored sources with explicit external dependencies

The five .tex/.bib files are byte-exact accepted V21 scientific sources.
This source distribution deliberately omits the six external class/BST/style
files in EXTERNAL_DEPENDENCIES.json. The supplied build adapter and relative
manifests replace the private flat distribution's transport metadata.
It is not the unchanged private15memberZIP or a self-contained TeX runtime.

Obtain the template from the publisher's official support page:
https://www.springernature.com/gp/authors/campaigns/latex-author-support
The exact original dependency archive and file fingerprints are recorded in
EXTERNAL_DEPENDENCIES.json. The other four .sty files are TeX runtime
dependencies. Supply all six matching external files in one flat directory
under their applicable terms, together with an installed pdflatex/BibTeX.
No third-party template or runtime code is redistributed in this archive.

Extract authored_source.zip, keep assertions enabled, then run:
  python -I -B build_with_dependencies.py --dependencies /absolute/external-dependencies --out /absolute/new-build --engine /path/to/pdflatex
For MiKTeX add --miktex. The output must be new, absolute and outside the
source directory. This fixed-release adapter checks all5authored source
hashes and all6external dependency hashes before running the installed
compiler. It disables shell escape and MiKTeX package installation, uses
the output directory for temporary files, and retains actual child exits.
The bibliography adapter only removes absent publisher-location placeholders;
all27references remain. No key, model call or scientific optimization occurs.

Only the recorded local environment is validated by LOCAL_DELIVERY_CHECK.json
in the parent reading directory. It compares the actual extracted build's
entire70-page text, decoded page-content streams, boxes and25label mappings
with the accepted reading PDF. It is not publisher-server conversion,
a new independent implementation, human review or a journal acceptance.

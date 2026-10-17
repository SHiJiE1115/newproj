V22 authored scientific sources with explicit external dependencies

All six scientific .tex/.bib files are exact accepted V22 bytes. This
10-member source ZIP is a declared distribution derivative of the private
16-member flat ZIP, not that unchanged archive. The six external class,
BST and style files listed in EXTERNAL_DEPENDENCIES.json are omitted.
The build adapter and relative manifests replace private transport files.

Obtain the external publisher template and TeX package dependencies under
their applicable terms. The official source locations and exact archived
file fingerprints are retained in EXTERNAL_DEPENDENCIES.json. Versions
are pinned to the recorded build; no latest-version equivalence is claimed.
Supply the six matching files in one external flat directory plus an
installed pdflatex/BibTeX. No external template/runtime code is included.

Keep assertions enabled. From the extracted source directory run:
  python -I -B build_with_dependencies.py --dependencies ABSOLUTE_EXTERNAL_DIRECTORY --out ABSOLUTE_NEW_BUILD_DIRECTORY --engine PATH_TO_PDFLATEX
For MiKTeX add --miktex. The output must be new, absolute and outside this
source directory. The adapter checks all6source and all6dependency hashes,
disables shell escape and MiKTeX package installation, directs temporary
files to the build directory, and retains actual child process exits.
The bibliography adapter removes only absent location placeholders;
all27references are retained. No model call or scientific optimization occurs.

LOCAL_DELIVERY_CHECK.json in the parent reading directory records the one
actual extracted-source rebuild and its page/label correspondence scope.
This is local delivery verification, not publisher-server compliance,
independent human review, a new scientific implementation or acceptance.

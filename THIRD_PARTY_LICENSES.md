# Third-party licenses

The following browser dependencies are bundled locally in `static/vendor/`. Their files retain upstream copyright and license notices.

| Library | Version | License | Original project |
| --- | --- | --- | --- |
| Three.js (including `OrbitControls` and `STLLoader`) | 0.160.0 (r160) | MIT | https://threejs.org/ |
| Marked | 15.0.12 | MIT | https://github.com/markedjs/marked |
| Highlight.js (including GitHub Dark style) | 11.9.0 | BSD-3-Clause | https://highlightjs.org/ |

Full license texts are included alongside each dependency:

## SimpleCADAPI

The application vendors and installs the repository-local
[SimpleCADAPI](SimpleCADAPI/) package (`2.0.4b1`) as its CAD runtime.  It is
licensed under the GNU Affero General Public License, version 3 (AGPL-3.0).
The complete license text is distributed in
[SimpleCADAPI/LICENSE](SimpleCADAPI/LICENSE), and the corresponding source is
distributed in this repository under `SimpleCADAPI/`.

SimpleCADAPI upstream project: <https://github.com/NiJingzhe/SimpleCADAPI>.
Changes to the vendored source remain subject to the AGPL-3.0 source and
corresponding-source obligations.  When distributing this application, keep
this notice, the license text, and the complete `SimpleCADAPI/` source
available to recipients.

- `static/vendor/three/LICENSE`
- `static/vendor/marked/LICENSE`
- `static/vendor/highlight/LICENSE`

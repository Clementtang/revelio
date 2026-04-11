# Third-Party Licenses

This project uses the following third-party libraries:

## EasyOCR

- **Version**: >=1.7.2
- **License**: Apache License 2.0
- **Repository**: https://github.com/JaidedAI/EasyOCR
- **Copyright**: Copyright (c) 2020 Jaided AI

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## NumPy

- **Version**: >=1.24.0
- **License**: BSD 3-Clause License
- **Repository**: https://github.com/numpy/numpy
- **Copyright**: Copyright (c) 2005-2024, NumPy Developers

```
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.
```

## Pillow

- **Version**: >=10.0.0
- **License**: HPND (Historical Permission Notice and Disclaimer)
- **Repository**: https://github.com/python-pillow/Pillow
- **Copyright**: Copyright (c) 1997-2011 by Secret Labs AB, Copyright (c) 1995-2011 by Fredrik Lundh and contributors

```
The Python Imaging Library (PIL) is

    Copyright (c) 1997-2011 by Secret Labs AB
    Copyright (c) 1995-2011 by Fredrik Lundh and contributors

Pillow is the friendly PIL fork. It is

    Copyright (c) 2010 by Jeffrey A. Clark and contributors

Like PIL, Pillow is licensed under the open source HPND License.
```

## Requests

- **Version**: >=2.31.0
- **License**: Apache License 2.0
- **Repository**: https://github.com/psf/requests
- **Copyright**: Copyright (c) 2019 Kenneth Reitz

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```

## MCP (Model Context Protocol)

- **Version**: >=1.0.0
- **License**: MIT License
- **Repository**: https://github.com/modelcontextprotocol
- **Copyright**: Copyright (c) Anthropic

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software.
```

---

## EasyOCR MCP Server (Code Reference)

- **Repository**: https://github.com/WindoC/easyocr-mcp
- **License**: Apache License 2.0
- **Note**: The MCP server implementation in `src/mcp-server/server.py` is based on this project.

License confirmed on 2025-02-03 via https://github.com/WindoC/easyocr-mcp/issues/1

---

## PyTorch (Transitive Dependency)

EasyOCR depends on PyTorch:

- **License**: BSD 3-Clause License
- **Repository**: https://github.com/pytorch/pytorch
- **Copyright**: Copyright (c) 2016-present, Facebook Inc.

---

## opendataloader-pdf (External Tool, Not Bundled)

- **Repository**: https://github.com/opendataloader-project/opendataloader-pdf
- **License**: Apache License 2.0
- **Usage**: Invoked as an external subprocess from the `/revelio` skill for PDF parsing. Users install it independently into their own Python venv (`~/odl-env/`) — Revelio does not bundle, redistribute, or modify this project's code. This listing is provided for transparency and attribution.

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```

---

## Summary

| Library            | License      | Integration           | Compatibility    |
| ------------------ | ------------ | --------------------- | ---------------- |
| EasyOCR            | Apache 2.0   | Python dependency     | ✓ MIT-compatible |
| NumPy              | BSD 3-Clause | Python dependency     | ✓ MIT-compatible |
| Pillow             | HPND         | Python dependency     | ✓ MIT-compatible |
| Requests           | Apache 2.0   | Python dependency     | ✓ MIT-compatible |
| MCP                | MIT          | Python dependency     | ✓ MIT-compatible |
| PyTorch            | BSD 3-Clause | Transitive dependency | ✓ MIT-compatible |
| opendataloader-pdf | Apache 2.0   | External subprocess   | ✓ MIT-compatible |

All dependencies and external tools are compatible with this project's MIT License.

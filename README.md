<p align="center">
  <img src="docs/images/vendor-banner.svg" alt="MCQN" width="560">
</p>

# MCQN ESP Board Manager Board Pack

[中文](README_CN.md)

This component provides ESP Board Manager YAML definitions for MCQN
development boards. Applications can install it from the
[ESP Component Registry](https://components.espressif.com) and select a board.

> Template note: Upload your vendor banner and board photos to `docs/images/`,
> then edit the image `src` paths and product links directly in both README files.

## Supported Boards

Choose a board by its photo and configured devices, then use its board ID with
`idf.py bmgr -b`. Click the photo or board name for product details or its
configuration directory.

The table summarizes nine configured capability categories: audio, SD card,
LCD, touch, camera, buttons, LED strip, knob, and Ethernet. It is not an
inventory of all physical hardware.

<!-- BEGIN SUPPORTED_BOARDS -->
### ESP32-S3

| Photo | Board | Chip | Device capabilities |
| --- | --- | --- | --- |
| <a href="example_board"><img src="docs/images/example_board.svg" alt="Example Board" width="120"></a> | <a href="example_board">Example Board</a><br><code>example_board</code> | ESP32-S3 | None of the listed capabilities |
| <img src="docs/images/example_board.svg" alt="Board photo" width="120"> | `miab` | ESP32-S3 | |

### ESP32-C3

| Photo | Board | Chip | Device capabilities |
| --- | --- | --- | --- |
| <img src="docs/images/example_board.svg" alt="Board photo" width="120"> | `my_bikes_got_led` | ESP32-C3 | |
<!-- END SUPPORTED_BOARDS -->

## Use This Pack in an Application

Install the helper once in the active ESP-IDF Python environment:

```bash
python -m pip install --upgrade esp-bmgr-assist
```

Add the released component, then select a board:

```bash
idf.py add-dependency "mcqn/esp_boards"
idf.py bmgr -l
idf.py bmgr -b <board_name>
idf.py build
```

The board pack already declares `espressif/esp_board_manager`; applications do
not need to add it again unless they need a tighter version constraint.

## Vendor Maintenance Guide

For creating a repository from this template, migrating an existing BSP,
configuring CI, and publishing the component, see
[VENDOR_GUIDE.md](VENDOR_GUIDE.md).

## License

This component uses Apache-2.0. Preserve and comply with existing copyright
notices and licenses when migrating a BSP or adding third-party content.

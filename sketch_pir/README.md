# Arduino project to handle the PIR motion sensor


This folder contains an Arduino project to handle the PIR motion sensor.
Use Arduino IDE to build and deploy to your device.

The code sends motion readings from the sensor in the form:

```json
{"motion": 0, "timestamp": 12345678}
{"motion": 1, "timestamp": 12346679}
{"motion": 0, "timestamp": 12356680}
```
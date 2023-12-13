int pirPin = 2;
int pirStat = 0;
unsigned long last_refresh_ms = 0;
const unsigned long HIGH_REFRESH = 1000;
const unsigned long FULL_REFRESH = 10000;

void setup() {
  pinMode(pirPin, INPUT);
  Serial.begin(115200);
  Serial.println("Serial Monitor connected.");
  Serial.print("Calibrating sensor...");
  Serial.flush();
  for (int i = 0; i < 10; i++) {
    Serial.print(".");
    Serial.flush();
    delay(1000);
  }
  Serial.println("ok");
}

unsigned long delayedPrint(String text, unsigned long lastRefresh, unsigned long interval_ms) {
  unsigned long time_ms = millis();  
  if (time_ms - lastRefresh > interval_ms) {
    Serial.println(text);
    lastRefresh = time_ms;
  }

  return lastRefresh;
}

void loop() {
  pirStat = digitalRead(pirPin);
  unsigned long time_ms = millis();
  if (pirStat == HIGH && time_ms - last_refresh_ms > HIGH_REFRESH || time_ms - last_refresh_ms > FULL_REFRESH) {
    char s[100];
    snprintf(s, sizeof(s), "{\"motion\": %d, \"timestamp\": %lu}", (int)(pirStat == HIGH), millis());
    Serial.println(s);
    last_refresh_ms = time_ms;
  }
}

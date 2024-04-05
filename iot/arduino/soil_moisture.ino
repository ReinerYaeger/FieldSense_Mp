#define AOUT_PIN_0 A0
#define AOUT_PIN_1 A1
#define AOUT_PIN_2 A2

void setup() {
  Serial.begin(9600);

}

void loop() {
  int a_out_array[5];

  //Connected to 5 Volts

  a_out_array[0] = analogRead(AOUT_PIN_0);
  a_out_array[1] = analogRead(AOUT_PIN_1);
  a_out_array[2] = analogRead(AOUT_PIN_2);

  float wet_base_value = 202.0;
  float dry_base_value = 488.0;
  float range = wet_base_value - dry_base_value;


  float moisture_0 = (a_out_array[0] - dry_base_value) / range;
  float moisture_1 = (a_out_array[1] - dry_base_value) / range;
  float moisture_2 = (a_out_array[2] - dry_base_value) / range;

  if (moisture_0<0){
    moisture_0 = 0;
  }
  if (moisture_1<0){
    moisture_1 = 0;
  }
  if (moisture_2<0){
    moisture_2 = 0;
  }

  //(float(analogRead(a_out_array[0]))/1023.0)*5
  Serial.print("A");
  Serial.print("0");
  Serial.print(": ");
  Serial.print(moisture_0,5);

  Serial.print("\t");

  Serial.print("A");
  Serial.print(1);
  Serial.print(": ");
  Serial.print(moisture_1,5);

  Serial.print("\t");

  Serial.print("A");
  Serial.print(2);
  Serial.print(": ");

  Serial.println(moisture_2,5);

  delay(1000);
}

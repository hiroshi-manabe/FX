//+------------------------------------------------------------------+
//|                                                   BitPattern.mq4 |
//|                                   Copyright 2022, Hiroshi Manabe |
//|                                                                  |
//+------------------------------------------------------------------+
#property strict

uint curIndex = 0;
uint prevIndex = 0;
uint priceList[10000];
uint timeList[10000];
uint timeWidths[];
double params[][5];
double trainingData[][10000][4];
double meanStd[][2][2];
uint prevTime;
uint waitTime = 300000;
uint trainingDataLengths[];
bool isDebug = false;

double maxLotPerPosition = 80;
int lossCutWidth = 50;

double minProfit = 0.000;
int priceToNormalize = 100000;
double accountBalanceForDebug = 1000000;

uint getPrice(int index) {
  int adjustedIndex = index % ArraySize(priceList);
  return priceList[adjustedIndex];
}

void setPrice(int index, uint value) {
  int adjustedIndex = index % ArraySize(priceList);
  priceList[adjustedIndex] = value;
}

uint getTime(int index) {
  int adjustedIndex = index % ArraySize(timeList);
  return timeList[adjustedIndex];
}

void setTime(int index, uint value) {
  int adjustedIndex = index % ArraySize(timeList);
  timeList[adjustedIndex] = value;
}

int findIndexBeforeMilliseconds(int index, uint milliseconds) {
  uint targetTime = getTime(index) - milliseconds;

  for (int i = index - 1; i >= 0; i--) {
    if (getTime(i) < targetTime) {
      return i + 1;
    }
  }

  return -1;
}

void readParams(int file_handle, double &data[][]) {
  while(!FileIsEnding(file_handle)) {
    string line = FileReadString(file_handle);
    string values[];
    int num_values = StringSplit(line, ',', values);
    double row[5] = {0};
    for (int i = 0; i < num_values; i++) {
      row[i] = StrToDouble(values[i]);
    }
    int data_rows = ArrayRange(data, 0);
    ArrayResize(data, data_rows + 1);
    for (int i = 0; i < ArraySize(row); ++i) {
      data[data_rows][i] = row[i];
    }
  }
  return;
}

void readTrainingData(int file_handle, const int &widths[], double &data[][10000][4], uint &lengths[], double &meanStdRef[][2][2]) {
  for (int i = 0; i < ArraySize(widths); i++) {
    lengths[i] = 0;
  }

  while (!FileIsEnding(file_handle)) {
    string line = FileReadString(file_handle);
    string parts[];
    StringSplit(line, ',', parts);
    if (ArraySize(parts) < 5) {
      Print("Invalid data format in input file.");
      continue;
    }

    int width = StrToInteger(parts[0]);
    double values[4];
    values[0] = StringToDouble(parts[1]);
    values[1] = StringToDouble(parts[2]);
    values[2] = StringToDouble(parts[3]);
    values[3] = StringToDouble(parts[4]);

    int index = ArrayBsearch(widths, width);
    if (index < 0) {
      Print("Time width not found in timeWidths array.");
      continue;
    }

    uint dataLength = lengths[index];
    if (dataLength >= 10000) {
      Print("Data size exceeded the limit of 10000.");
      break;
    }

    for (int i = 0; i < 4; i++) {
      data[index][dataLength][i] = values[i];
    }
    lengths[index]++;
  }

  for (int i = 0; i < ArraySize(widths); i++) {
    for (int j = 0; j <= 1; j++) {
      double sum = 0;
      for (uint k = 0; k < lengths[i]; k++) {
        sum += data[i][k][j];
      }
      double mean = sum / lengths[i];

      double squaredDiffSum = 0;
      for (uint k = 0; k < lengths[i]; k++) {
        squaredDiffSum += MathPow(data[i][k][j] - mean, 2);
      }
      double stdDev = MathSqrt(squaredDiffSum / lengths[i]);

      meanStdRef[i][j][0] = mean;
      meanStdRef[i][j][1] = stdDev;
    }
  }
  for (int i = 0; i < ArraySize(widths); i++) {
    for (uint j = 0; j < lengths[i]; j++) {
      for (int k = 0; k <= 1; k++) {
        double original_value = data[i][j][k];
        double mean = meanStdRef[i][k][0];
        double stdDev = meanStdRef[i][k][1];
        double normalized_value = (original_value - mean) / stdDev;
        data[i][j][k] = normalized_value;
      }
    }
  }
}

struct OrderInfo {
  int ticket;
  uint time;
  uint timeWidth;
  double price;
  double lot;
  bool isSell;
  bool isActive;
};

OrderInfo order;

int handleOrder = INVALID_HANDLE;
int handleTicks = INVALID_HANDLE;
bool orderOnceForDebug = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
  int handleParams = FileOpen("params.csv", FILE_READ | FILE_CSV | FILE_COMMON);
  readParams(handleParams, params);
  FileClose(handleParams);
  ArrayResize(timeWidths, ArrayRange(params, 0));
  ArrayResize(trainingData, ArraySize(params));
  ArrayResize(trainingDataLengths, ArraySize(params));
  ArrayResize(meanStd, ArraySize(params));
  for (int i = 0; i < ArraySize(timeWidths); ++i) {
    timeWidths[i] = (uint)params[i][0];
  }

  datetime current_time = TimeCurrent();
  string current_time_str = IntegerToString(TimeYear(current_time), 4) + "-" +
    IntegerToString(TimeMonth(current_time), 2) + "-" +
    IntegerToString(TimeDay(current_time), 2) + "-" +
    IntegerToString(TimeHour(current_time), 2) + "-" +
    IntegerToString(TimeMinute(current_time), 2) + "-" +
    IntegerToString(TimeSeconds(current_time), 2);

  handleOrder = FileOpen("order_" + current_time_str + ".csv", FILE_WRITE | FILE_CSV);   

  order.ticket = INVALID_HANDLE;
  order.isActive = false;

  int handleTrainingData = FileOpen("training_data.csv", FILE_READ | FILE_CSV | FILE_COMMON);
  readTrainingData(handleTrainingData, timeWidths, trainingData, trainingDataLengths, meanStd);
  FileClose(handleTrainingData);
  if (isDebug) {
    OnTick();
  }

  //---
  return(INIT_SUCCEEDED);
}
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
  //--- destroy timer
  if (handleOrder != INVALID_HANDLE) {
    FileClose(handleOrder);
  }
  if (handleTicks != INVALID_HANDLE) {
    FileClose(handleTicks);
  }
}

void k_nearest_neighbors(double first_coef, double second_coef,
                          const double &train_data[][][],
                          uint &lengths[], uint timeWidthIndex,
                          int &output_array[], int k) {
  double neighbors[][2];
  uint length = lengths[timeWidthIndex];
  ArrayResize(neighbors, length);
  for (uint i = 0; i < length; i++) {
    double distance = MathPow(train_data[timeWidthIndex][i][0] - first_coef, 2) + MathPow(train_data[timeWidthIndex][i][1] - second_coef, 2);
    neighbors[i][0] = distance;
    neighbors[i][1] = i;
  }
  ArraySort(neighbors);

  for (uint i = 0; i < k; ++i) {
    output_array[i] = neighbors[i][1];
  }
}

bool fitIt(const double &X[], const double &Y[], double &coeffs[]) {
  int n = 2;
  int np1 = n + 1;
  int np2 = n + 2;
  int tnp1 = 2 * n + 1;
  double tmp;
  double a[3] = {0};
  double B[3][4] = {0};
  coeffs[0] = -99999;

  for (int i = 0; i <= n; ++i) {
    for (int j = 0; j <= n; ++j) {
      B[i][j] = X[i + j];
    }
  }

  for (int i = 0; i <= n; ++i) {
    B[i][np1] = Y[i];
  }

  n += 1;
  int nm1 = n - 1;

  for (int i = 0; i < n; ++i) {
    for (int k = i + 1; k < n; ++k) {
      if (B[i][i] < B[k][i]) {
        for (int j = 0; j <= n; ++j) {
          tmp = B[i][j];
          B[i][j] = B[k][j];
          B[k][j] = tmp;
        }
      }
    }
  }

  for (int i = 0; i < nm1; ++i) {
    for (int k = i + 1; k < n; ++k) {
      if (B[i][i] == 0) {
        return false;
      }
      double t = B[k][i] / B[i][i];
      for (int j = 0; j <= n; ++j) {
        B[k][j] -= t * B[i][j];
      }
    }
  }

  for (int i = nm1; i >= 0; --i) {
    a[i] = B[i][n];
    for (int j = 0; j < n; ++j) {
      if (j != i) {
        a[i] -= B[i][j] * a[j];
      }
    }
    a[i] /= B[i][i];
  }

  for (int i = 0; i < 3; ++i) {
    coeffs[i] = a[i];
  }

  return true;
}

double quadratic(double x, double a, double b, double c) {
  return a * x * x + b * x + c;
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+

void OnTick() {
  if (isDebug) {
    int handle_tick = FileOpen("tick_data.csv", FILE_READ | FILE_CSV | FILE_COMMON);
    while(!FileIsEnding(handle_tick)) {
      string line = FileReadString(handle_tick);
      string values[];
      StringSplit(line, ',', values);
      double doubleValues[2] = {0};
      for (int i = 1; i < 3; i++) {
        doubleValues[i-1] = StrToDouble(values[i]);
      }
      uint tickCount = StrToInteger(values[0]);
      OnTickMain(tickCount, doubleValues[0] / 1000, doubleValues[1] / 1000);
    }
  }
  OnTickMain(GetTickCount(), Ask, Bid);
}

void OnTickMain(uint tickCount, double ask, double bid) {
  int nAsk = (int)(ask * 1000);
  int nBid = (int)(bid * 1000);
  
  datetime current_time = TimeCurrent();
  string tickDataFileName = StringFormat("ticks-%04d-%02d-%02d-%02d.csv",
                                         TimeYear(current_time),
                                         TimeMonth(current_time),
                                         TimeDay(current_time),
                                         TimeHour(current_time));

  if (handleTicks == INVALID_HANDLE || !FileIsExist(tickDataFileName)) {
    if (handleTicks != INVALID_HANDLE) {
      FileClose(handleTicks);
    }
    handleTicks = FileOpen(tickDataFileName, FILE_WRITE | FILE_CSV, ',');
  }

  setPrice(curIndex, nAsk);
  uint curTime = tickCount;
  setTime(curIndex, curTime);
  uint c = curIndex;
  curIndex++;

  double rate = (double)nAsk / priceToNormalize;
  
  bool spreadIsWide = ask > bid + 0.009;
  if (spreadIsWide) {
    FileWrite(handleTicks, getTime(c), nAsk, nBid);
    return;
  }
  if (order.isActive) {
    bool closeFlag = false;
    if (curTime > order.time + order.timeWidth / 4) {
      int beforeIndex = findIndexBeforeMilliseconds(c, (int)(order.timeWidth / 4));
      uint beforePrice = getPrice(beforeIndex);
      if ((!order.isSell &&
           ask <= beforePrice + minProfit) ||
          (order.isSell &&
           ask >= beforePrice - minProfit)) {
        closeFlag = true;
      }
    }
    if (closeFlag) {
      int handle_signal = FileOpen("signal_close.csv", FILE_WRITE | FILE_CSV | FILE_COMMON);
      FileWrite(handle_signal, "Close");
      FileClose(handle_signal);
      
      if (order.ticket != INVALID_HANDLE) {
        Print("オーダークローズ");
        FileWrite(handleOrder, "Order close, time:" + IntegerToString(tickCount));
        order.ticket = INVALID_HANDLE;
      }
      double pl = ((order.isSell ? order.price - ask : ask - order.price) - 0.005) * order.lot * 100000;
      Print("仮想的損益: ", pl);
      if (isDebug) {
        accountBalanceForDebug += pl;
        Print("仮想的残高: ", accountBalanceForDebug);
      }
      order.isActive = false;
    }
    if (order.isActive) {
      FileWrite(handleTicks, tickCount, nAsk, nBid);
      return;
    }
  }
  string outputStr = "";
  for (uint i = 0; i < (uint)ArraySize(timeWidths); ++i) {
    uint timeWidth = timeWidths[i];
    int j = findIndexBeforeMilliseconds(c, timeWidths[i]);
    if (j == -1) {
      continue;
    }
    double X[5] = {0};
    double Y[3] = {0};
    for (uint k = j; k <= c; ++k) {
      double x = (double)getTime(k) - curTime;
      double y = (double)getPrice(k) / rate - priceToNormalize;
      X[0] += 1;
      X[1] += x;
      double t = x * x;
      X[2] += t;
      t *= x;
      X[3] += t;
      t *= x;
      X[4] += t;
      t = y;
      Y[0] += t;
      t *= x;
      Y[1] += t;
      t *= x;
      Y[2] += t;
    }
    double coeffs[3];
    if (X[0] == 0 || !fitIt(X, Y, coeffs)) {
      continue;
    }
    double y_mean = Y[0] / X[0];
    double ss_res = 0.0;
    double ss_tot = 0.0;
        
    for (uint k = j; k <= c; ++k) {
      uint time = getTime(k);
      double price = (double)getPrice(k) / rate;
      double x = (double)time - curTime;
      double y = (double)price - priceToNormalize;
      double y_pred = quadratic(x, coeffs[2], coeffs[1], coeffs[0]);
      double t = y - y_pred;
      ss_res += t * t;
      t = y - y_mean;
      ss_tot += t * t;
    }
    if (ss_tot == 0) {
      continue;
    }
    double r_squared = 1 - (ss_res / ss_tot);

    string action = orderOnceForDebug ? "buy" : "pass";
    uint indexBeforeWindow = findIndexBeforeMilliseconds(c, timeWidth);
    
    if (MathAbs(coeffs[0]) <= 3.0 && r_squared >= params[i][1] &&
        indexBeforeWindow != c && timeWidth / (c - indexBeforeWindow) <= 400 &&
        curTime > prevTime + waitTime) {
      int k = (int)params[i][2];
      int output_array[];
      ArrayResize(output_array, k);
      int threshold = (int)params[i][3];
      double first_coef = (coeffs[1] - meanStd[i][0][0]) / meanStd[i][0][1];
      double second_coef = (coeffs[2] - meanStd[i][1][0]) / meanStd[i][1][1]; 
      k_nearest_neighbors(first_coef, second_coef,
                          trainingData, trainingDataLengths, i,
                          output_array,
                          k);

      double avr_x = 0.0;
      double avr_y = 0.0;
      
      for(int l = 0; l < k; l++){
        avr_x += trainingData[i][output_array[l]][0];
        avr_y += trainingData[i][output_array[l]][1];
      }
      avr_x = avr_x / k;
      avr_y = avr_y / k;

      double distance_to_center = MathSqrt(MathPow((first_coef - avr_x), 2) + MathPow((second_coef - avr_y), 2));
      double radius = MathSqrt(MathPow((first_coef - trainingData[i][output_array[k - 1]][0]), 2) + MathPow((second_coef - trainingData[i][output_array[k - 1]][1]), 2));
      if (distance_to_center > radius / 2){
        continue;
      }

      int results[2] = {0};
      int t = 20;

      for(int col_offset = 0; col_offset < 2; col_offset++){
        int plus_minus = 0;
        for(int l = 0; l < k; l++){
          int col_index = 2 + col_offset;
          double pl = trainingData[i][output_array[l]][col_index];
          if (pl >= t){
            results[col_offset] += 1;
          }
          else if (pl <= -t){
            results[col_offset] -= 1;
          }
        }
      }

      if (results[0] >= threshold) {
        action = "buy";
      }
      else if (results[1] >= threshold) {
        action = "sell";
      }
      else {
        action = "pass";
      }
      prevTime = curTime;
    }
    if (order.ticket == INVALID_HANDLE && action != "pass") {
      orderOnceForDebug = false;
      if (FileIsExist("signal_close.csv", FILE_COMMON)) {
        FileDelete("signal_close.csv", FILE_COMMON);
      }
      bool isSell = (action == "sell");
       
      string orderStr = "Order time: " + IntegerToString(tickCount) + 
        " timeWidth: " + IntegerToString(timeWidths[i]) + 
        " coeffs: " + DoubleToString(coeffs[1]) + "/" + DoubleToString(coeffs[2]) + 
        " " + action;
      double fraction = params[i][4];
      int handle_signal = FileOpen("signal.csv", FILE_WRITE | FILE_CSV | FILE_COMMON);
      FileWrite(handle_signal, IntegerToString(tickCount) + "," +
                action + "," + DoubleToString(fraction) + "," +
                orderStr);
      FileClose(handle_signal);
                                    
      double price = isSell ? bid : ask;
      double closePrice = isSell ? ask : bid;

      double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      if (isDebug) {
        accountBalance = accountBalanceForDebug;
      }

      double maxBet = accountBalance * 495 / ask;
      double bet = accountBalance * 1000 * (fraction / 2);
      bet = maxBet;
      double lot = double(int(bet / 1000)) / 100;
      int ticket = INVALID_HANDLE;
      ticket = OrderSend(Symbol(),
                         isSell ? OP_SELL : OP_BUY,
                         lot,
                         price,
                         10,
                         isSell ? closePrice + lossCutWidth : closePrice - lossCutWidth,
                         0);

      if (isDebug) {
        ticket = 1;
      }
      if (ticket != INVALID_HANDLE) {
        order.ticket = ticket;
        order.isActive = true;
      }
      else {
        Print("オーダーエラー：エラーコード=", GetLastError());
      }
      if (accountBalance == 0) {
          order.ticket = 0;
          order.isActive = true;
      }
      if (order.isActive) {
        Print(orderStr);
        FileWrite(handleOrder, orderStr);
        order.time = curTime;
        order.timeWidth = timeWidth;
        order.price = ask;
        order.lot = lot;
        order.isSell = (action == "sell");
      }
    }
    outputStr += StringConcatenate(coeffs[0], ",", coeffs[1], ",", coeffs[2], ",", r_squared);
    if (i < (uint)ArraySize(timeWidths) - 1) {
      outputStr += "/";
    }
  }
  FileWrite(handleTicks, tickCount, nAsk, nBid, outputStr);
}
//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer() {
  //---
   
}
//+------------------------------------------------------------------+
//| Tester function                                                  |
//+------------------------------------------------------------------+
double OnTester() {
  //---
  double ret=0.0;
  //---

  //---
  return(ret);
}
//+------------------------------------------------------------------+

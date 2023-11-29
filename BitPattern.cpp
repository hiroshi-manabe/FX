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
double params[][5];
double trainingData[][10000][4];
double meanStd[][2][2];
uint prevTime;
uint waitTime = 300000;
uint trainingDataLengths[];
bool isDebug = false;
int mode = 1; // 1 for standalone, 2 for sending, and 3 for receiving mode

double maxLotPerPosition = 80;
double lossCutWidth = 0.05;

double minProfit = 0;
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
  while (!FileIsEnding(file_handle)) {
    string line = FileReadString(file_handle);
    string values[];
    int num_values = StringSplit(line, ',', values);
    double row[4] = {0};
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

void readTrainingData(int file_handle, double &data[][10000][4], uint &lengths[], double &meanStdRef[][2][2]) {
  int dataLen = ArrayRange(data, 0);
  for (int i = 0; i < dataLen; i++) {
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

    int index = StrToInteger(parts[0]);
    uint dataLength = lengths[index];
    if (dataLength >= 10000) {
      Print("Data size exceeded the limit of 10000.");
      break;
    }

    for (int i = 0; i < 4; i++) {
      data[index][dataLength][i] = StrToDouble(parts[i+1]);
    }
    lengths[index]++;
  }

  for (int i = 0; i < dataLen; i++) {
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
  for (int i = 0; i < dataLen; i++) {
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
int handleDebugInput = INVALID_HANDLE;
int leverage = 390;
string leverageFileName = "leverage.csv";
string currentFileName = "";
bool orderOnceForDebug = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
  int handleParams = FileOpen("params.csv", FILE_READ | FILE_CSV | FILE_COMMON);
  readParams(handleParams, params);
  FileClose(handleParams);
  ArrayResize(trainingData, ArrayRange(params, 0));
  ArrayResize(trainingDataLengths, ArrayRange(params, 0));
  ArrayResize(meanStd, ArrayRange(params, 0));

  if (FileIsExist(leverageFileName, FILE_COMMON)) {
    int fileHandle = FileOpen(leverageFileName, FILE_READ | FILE_COMMON);
    string str = FileReadString(fileHandle);
    leverage = StrToInteger(str);
    FileClose(fileHandle);
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
  readTrainingData(handleTrainingData, trainingData, trainingDataLengths, meanStd);
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
  if (handleDebugInput != INVALID_HANDLE) {
    FileClose(handleDebugInput);
  }
}

bool MyOrderSelect(int index, int select, int pool=MODE_TRADES) {
    Print("MyOrderSelect called with index: ", index, ", select: ", select);
    if(!isDebug) {
        return OrderSelect(index, select, pool);
    }
    return true;
}

int MyOrderSend(
    string symbol, 
    int cmd, 
    double volume, 
    double price, 
    int slippage, 
    double stoploss, 
    double takeprofit, 
    string comment=NULL, 
    int magic=0, 
    datetime expiration=0, 
    color arrow_color=clrNONE
) {
    Print("MyOrderSend called with symbol: ", symbol, ", cmd: ", cmd, ", volume: ", volume, ", price: ", price, ", slippage: ", slippage, ", stoploss: ", stoploss, ", takeprofit: ", takeprofit);

    if(!isDebug) {
        return OrderSend(symbol, cmd, volume, price, slippage, stoploss, takeprofit, comment, magic, expiration, arrow_color);
    }
    return 1;
}

bool MyOrderClose(
    int ticket, 
    double lots, 
    double price, 
    int slippage, 
    color arrow_color=CLR_NONE
) {
    Print("MyOrderClose called with ticket: ", ticket, ", lots: ", lots, ", price: ", price, ", slippage: ", slippage);
    if(!isDebug) {
        return OrderClose(ticket, lots, price, slippage, arrow_color);
    }
    return true;
}

double MyOrderLots() {
  return isDebug ? 1.0 : OrderLots();
}

void k_nearest_neighbors(double first_coef, double second_coef,
                          const double &train_data[][][],
                          uint &lengths[], uint timeWidthIndex,
                          int &output_array[], uint k) {
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
    output_array[i] = (int)neighbors[i][1];
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
    handleDebugInput = FileOpen("tick_data.csv", FILE_READ | FILE_CSV | FILE_COMMON);
    while (!FileIsEnding(handleDebugInput)) {
      string line = FileReadString(handleDebugInput);
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
  else {
    datetime current_time = TimeCurrent();
    string tickDataFileName = StringFormat("ticks-%04d-%02d-%02d-%02d.csv",
                                           TimeYear(current_time),
                                           TimeMonth(current_time),
                                           TimeDay(current_time),
                                           TimeHour(current_time));
    if (handleTicks == INVALID_HANDLE) {
      handleTicks = FileOpen(tickDataFileName, FILE_WRITE | FILE_CSV, ',');
      currentFileName = tickDataFileName;
    }
    else if (tickDataFileName != currentFileName) {
      FileClose(handleTicks);
      handleTicks = FileOpen(tickDataFileName, FILE_WRITE | FILE_CSV, ',');
      currentFileName = tickDataFileName;
    }
    OnTickMain(GetTickCount(), Ask, Bid);
  }
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
  FileWrite(handleTicks, getTime(c), Ask, Bid);

  double rate = (double)nAsk / priceToNormalize;
  
  bool spreadIsWide = ask > bid + 0.009;
  if (spreadIsWide) {
    return;
  }
  if (order.isActive) {
    bool closeFlag = false;
    if (mode == 1 || mode == 2) {
      if (curTime > order.time + order.timeWidth / 4) {
        int beforeIndex = findIndexBeforeMilliseconds(c, (int)(order.timeWidth / 4));
        uint beforePrice = getPrice(beforeIndex);
        if ((!order.isSell &&
             nAsk <= beforePrice + minProfit) ||
            (order.isSell &&
             nAsk >= beforePrice - minProfit)) {
          closeFlag = true;
        }
        if (mode == 2 && closeFlag) {
          int handle_signal = FileOpen("signal_close.csv", FILE_WRITE | FILE_CSV | FILE_COMMON);
          FileWrite(handle_signal, "Close");
          FileClose(handle_signal);
        }
      }
    }
    else if (mode == 3) {
      if (FileIsExist("signal_close.csv", FILE_COMMON)) {
        closeFlag = true;
        FileDelete("signal_close.csv", FILE_COMMON);
      }
    }
    if (closeFlag) {
      if (order.ticket != INVALID_HANDLE) {
        Print("オーダークローズ");
        FileWrite(handleOrder, "Order close, time:" + IntegerToString(tickCount));
        if (mode == 1 || mode == 3) {
          MyOrderSelect(order.ticket, SELECT_BY_TICKET);
          MyOrderClose(order.ticket,
                       MyOrderLots(),
                       order.isSell ? ask : bid,
                       20);
        }
        order.ticket = INVALID_HANDLE;
      }
      order.isActive = false;
    }
    if (order.isActive) {
      return;
    }
  }
  string finalAction = "pass";
  string orderStr = "";
  uint timeWidth = 0;
  if (mode == 1 || mode == 2) {
    for (uint i = 0; i < (uint)ArrayRange(params, 0); ++i) {
      timeWidth = (uint)params[i][0];
      double r_squared_param = params[i][1];
      uint k_value = (uint)params[i][2];
      uint threshold = (uint)params[i][3];
      int j = findIndexBeforeMilliseconds(c, timeWidth);
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
      double first_coef = 0.0;
      double second_coef = 0.0;
    
      if (MathAbs(coeffs[0]) <= 3.0 && r_squared >= r_squared_param &&
          indexBeforeWindow != c && timeWidth / (c - indexBeforeWindow) <= 220 &&
          curTime > prevTime + waitTime) {

        int output_array[];
        ArrayResize(output_array, k_value);

        first_coef = (coeffs[1] - meanStd[i][0][0]) / meanStd[i][0][1];
        second_coef = (coeffs[2] - meanStd[i][1][0]) / meanStd[i][1][1];
        Print("Executing knn - time width: ", timeWidth,
              " coeffs: " + DoubleToString(first_coef) + "/"
              + DoubleToString(second_coef));
        k_nearest_neighbors(first_coef, second_coef,
                            trainingData, trainingDataLengths, i,
                            output_array,
                            k_value);

        double avr_x = 0.0;
        double avr_y = 0.0;
      
        for(uint l = 0; l < k_value; l++){
          avr_x += trainingData[i][output_array[l]][0];
          avr_y += trainingData[i][output_array[l]][1];
        }
        avr_x = avr_x / k_value;
        avr_y = avr_y / k_value;

        double distance_to_center = MathSqrt(MathPow((first_coef - avr_x), 2) + MathPow((second_coef - avr_y), 2));
        double radius = MathSqrt(MathPow((first_coef - trainingData[i][output_array[k_value - 1]][0]), 2) + MathPow((second_coef - trainingData[i][output_array[k_value - 1]][1]), 2));
        if (distance_to_center > radius / 2){
          Print("Distance to center to long.");
          continue;
        }

        int results[2] = {0};
        int t = 20;

        for(int col_offset = 0; col_offset < 2; col_offset++){
          int plus_minus = 0;
          for(uint l = 0; l < k_value; l++){
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
        if (results[0] >= (int)threshold) {
          action = "buy";
        }
        else if (results[1] >= (int)threshold) {
          action = "sell";
        }
        else {
          action = "pass";
        }
        Print("Threshold: ", threshold,
              " buy result: ", results[0],
              " sell result: ", results[1],
              " action: ", action);
      }
      if (action != "pass") {
        finalAction = action;
        orderStr = "Order time: " + IntegerToString(tickCount) + 
          " time width: " + IntegerToString(timeWidth) + 
          " coeffs: " + DoubleToString(first_coef) + "/" + DoubleToString(second_coef) + 
          " " + action;
        break;
      }
    }
    if (finalAction != "pass") {
      if (mode == 2) {
        if (FileIsExist("signal_close.csv", FILE_COMMON)) {
          FileDelete("signal_close.csv", FILE_COMMON);
        }
        int handle_signal = FileOpen("signal_" + finalAction + ".csv", FILE_WRITE | FILE_COMMON);
        FileWrite(handle_signal, orderStr);
        FileClose(handle_signal);
      }
    }
  }
  else if (mode == 3) {
    string actions[2] = {"buy", "sell"};
    for (int i = 0; i < 2; ++i) {
      string filename = "signal_" + actions[i] + ".csv";
      if (FileIsExist(filename, FILE_COMMON)) {
        finalAction = actions[i];
        int handle_signal = FileOpen(filename, FILE_READ | FILE_COMMON);
        orderStr = FileReadString(handle_signal);
        FileClose(handle_signal);
      }
    }
  }
  if (finalAction != "pass") {
    orderOnceForDebug = false;
    prevTime = curTime;
    bool isSell = (finalAction == "sell");
    double price = isSell ? bid : ask;
    double closePrice = isSell ? ask : bid;

    double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    if (isDebug) {
      accountBalance = accountBalanceForDebug;
    }

    double bet = accountBalance * leverage / ask;
    double lot = double(int(bet / 1000)) / 100;
    if (lot > 80) {
      lot = 80;
    }
    int ticket = INVALID_HANDLE;
    if (mode == 1 || mode == 3) {
      ticket = MyOrderSend(Symbol(),
                           isSell ? OP_SELL : OP_BUY,
                           lot,
                           price,
                           10,
                           isSell ? closePrice + lossCutWidth : closePrice - lossCutWidth,
                           0);
    }
    else if (mode == 2) {
      ticket = 0;
    }

    if (ticket != INVALID_HANDLE) {
      order.ticket = ticket;
      order.isActive = true;
    }
    else {
      Print("オーダーエラー：エラーコード=", GetLastError());
    }
    if (order.isActive) {
      Print(orderStr);
      FileWrite(handleOrder, orderStr);
      order.time = curTime;
      order.timeWidth = timeWidth;
      order.price = ask;
      order.lot = lot;
      order.isSell = (finalAction == "sell");
    }
  }
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

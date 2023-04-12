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
double minProfit = 0.000;
int priceToNormalize = 100000;

struct OrderInfo {
  int tickets[100];
  uint time;
  uint timeWidth;
  double coeffs[3];
  double price;
  bool isSell;
  bool isActive;
};

OrderInfo order;


int handleOrder = INVALID_HANDLE;
int handleTicks = INVALID_HANDLE;
bool orderOnceForDebug = false;

uint movementAboveThresholdTime = 0;

bool isMovementAboveThreshold = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
  datetime current_time = TimeCurrent();
  string current_time_str = IntegerToString(TimeYear(current_time), 4) + "-" +
                         IntegerToString(TimeMonth(current_time), 2) + "-" +
                         IntegerToString(TimeDay(current_time), 2) + "-" +
                         IntegerToString(TimeHour(current_time), 2) + "-" +
                         IntegerToString(TimeMinute(current_time), 2) + "-" +
                         IntegerToString(TimeSeconds(current_time), 2);

  handleOrder = FileOpen("order_" + current_time_str + ".csv", FILE_WRITE | FILE_CSV);   

  for (uint i = 0; i < 100; ++i) {
    order.tickets[i] = INVALID_HANDLE;
  }
  order.isActive = false;
  //---
  return(INIT_SUCCEEDED);
}
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
  //--- destroy timer
  if (handleOrder != INVALID_HANDLE) {
    FileClose(handleOrder);
  }
  if (handleTicks != INVALID_HANDLE) {
    FileClose(handleTicks);
  }
}

bool fitIt(const double &X[], const double &Y[], double &coeffs[])
{
   int n = 2;
   int np1 = n + 1;
   int np2 = n + 2;
   int tnp1 = 2 * n + 1;
   double tmp;

   double a[3] = {0};

   double B[3][4] = {0};

   for (int i = 0; i <= n; ++i)
   {
      for (int j = 0; j <= n; ++j)
      {
         B[i][j] = X[i + j];
      }
   }

   for (int i = 0; i <= n; ++i)
   {
      B[i][np1] = Y[i];
   }

   n += 1;
   int nm1 = n - 1;

   for (int i = 0; i < n; ++i)
   {
      for (int k = i + 1; k < n; ++k)
      {
         if (B[i][i] < B[k][i])
         {
            for (int j = 0; j <= n; ++j)
            {
               tmp = B[i][j];
               B[i][j] = B[k][j];
               B[k][j] = tmp;
            }
         }
      }
   }

   for (int i = 0; i < nm1; ++i)
   {
      for (int k = i + 1; k < n; ++k)
      {
         double t = B[k][i] / B[i][i];
         for (int j = 0; j <= n; ++j)
         {
            B[k][j] -= t * B[i][j];
         }
      }
   }

   for (int i = nm1; i >= 0; --i)
   {
      a[i] = B[i][n];
      for (int j = 0; j < n; ++j)
      {
         if (j != i)
         {
            a[i] -= B[i][j] * a[j];
         }
      }
      a[i] /= B[i][i];
   }

   for (int i = 0; i < 3; ++i)
   {
      coeffs[i] = a[i];
   }

   return true;
}

void setTimeList(uint curIndex, uint value) {
  uint bufSize = ArraySize(timeList);
  timeList[curIndex % bufSize] = value;
}

uint getTimeList(uint curIndex) {
  uint bufSize = ArraySize(timeList);
  return timeList[curIndex % bufSize];
}

void setPriceList(uint curIndex, double value) {
  uint bufSize = ArraySize(priceList);
  priceList[curIndex % bufSize] = value;
}

double getPriceList(uint curIndex) {
  uint bufSize = ArraySize(priceList);
  return (double)priceList[curIndex % bufSize];
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
  int nAsk = (int)(Ask * 1000);
  int nBid = (int)(Bid * 1000);
  
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

  setPriceList(curIndex, nAsk);
  uint curTime = GetTickCount();
  setTimeList(curIndex, curTime);
  prevIndex = curIndex - 1;
  curIndex++;

  double rate = (double)nAsk / priceToNormalize;
  
  bool spreadIsWide = Ask > Bid + 0.009;
  if (spreadIsWide || isMovementAboveThreshold) {
    FileWrite(handleTicks, GetTickCount(), nAsk, nBid);
    return;
  }
  if (order.isActive) {
    bool closeFlag = false;
    if (curTime > order.time + order.timeWidth / 4) {
      ...
      if ((!order.isSell &&
           Ask <= order.prevPrice + minProfit) ||
          (order.isSell &&
           Ask >= order.prevPrice - minProfit)) {
        closeFlag = true;
      }
      else {
        order.prevChecked += checkInterval;
        order.prevPrice = Ask;
      }
    }
    if (closeFlag) {
      int handle_signal = FileOpen("signal_close.csv", FILE_WRITE | FILE_CSV | FILE_COMMON);
      FileWrite(handle_signal, "Close");
      FileClose(handle_signal);
      
      for (uint i = 0; i < 100; ++i) {
        if (order.tickets[i] == INVALID_HANDLE) {
          continue;
        }
        Print("オーダークローズ");
        FileWrite(handleOrder, "Order close, time:" + IntegerToString(GetTickCount()));
            order.tickets[i] = INVALID_HANDLE;
      }
      order.isActive = false;
    }
    if (order.isActive) {
      FileWrite(handleTicks, GetTickCount(), nAsk, nBid);
      return;
    }
  }
  for (uint i = 0; i < ArraySize(timeWidths); ++i) {
    uint startTime = curTime - timeWidths[i] + 1;
    uint j = curTime;
    bool isOk = true;
    
    while (1) {
      if (getTimeList(j) < startTime) {
        break;
      } 
      uint time = getTimeList(j);
      uint price = int((double)getPriceList(j) / rate);
      int timeDiff = time - startTime;
      j--;
    }
    
    if (!isOk && !orderOnceForDebug) {
      continue;
    }
    

    j = c;
    while (1) {
      if (timeList[j] < startTime) {
        break;
      }
      uint time = timeList[j];
      uint price = int((double)priceList[j] / rate);
      int timeDiff = time - startTime;
      j = (j + bufSize - 1) % bufSize;
    }
    for (uint k = 0; k < (uint)ArraySize(features); ++k) {
      Feature f = features[k];
      double lossCutWidth = 0.05;
      if (orderOnceForDebug || order.tickets[0] == INVALID_HANDLE &&
          timeWidths[i] >= f.minWidth &&
          timeWidths[i] <= f.maxWidth &&
          priceFactor >= f.minHeight &&
          priceFactor <= f.maxHeight &&
          bitPatternStr == f.bitPatternStr) {
        orderOnceForDebug = false;
        if (FileIsExist("signal_close.csv", FILE_COMMON)) {
          FileDelete("signal_close.csv", FILE_COMMON);
        }
        
        int handle_signal = FileOpen("signal.csv", FILE_WRITE | FILE_CSV | FILE_COMMON);
        FileWrite(handle_signal, GetTickCount() + "," +
                                 (f.isSell ? "sell" : "buy") + "," +
                                 lossCutWidth + "," +
                                 f.origStr);
        FileClose(handle_signal);
                                    
        double price = f.isSell ? Bid : Ask;
        double closePrice = f.isSell ? Ask : Bid;

        // stub
        order.tickets[0] = 1;
        order.isActive = true;
        // stub end

        /*
        double maxBet = (double)(int(AccountInfoDouble(ACCOUNT_BALANCE) * 0.023 / price) - 1) / 100.0;
        int parts = int((maxBet + 10) / 10);
        double bet = (double)int(maxBet * 10 / parts) / 10.0;
        for (uint l = 0; l < parts; ++l) {
          int ticket = OrderSend(Symbol(),
                    f.isSell ? OP_SELL : OP_BUY,
                    bet,
                    price,
                    10,
                    f.isSell ? closePrice + lossCutWidth : closePrice - lossCutWidth,
                    0);
          int ticket = 1;
          if (ticket != INVALID_HANDLE) {
            order.tickets[l] = ticket;
            order.isActive = true;
          }
          else {
            Print("オーダーエラー：エラーコード=", GetLastError());
          }
        }
        */
        if (order.isActive) {
          string orderStr = "Order, time: " + IntegerToString(GetTickCount()) + 
            " timeWidth: " + IntegerToString(timeWidths[i]) + 
            " scale: " + IntegerToString(priceFactor) +
            " feature: " + f.origStr + 
            " " + (f.isSell ? "sell" : "buy");
          Print(orderStr);
          FileWrite(handleOrder, orderStr);
          order.time = curTime;
          order.prevChecked = 0;
          order.prevPrice = Ask;
          order.isSell = f.isSell;
        }
      }
    }
  }
  FileWrite(handleTicks, GetTickCount(), nAsk, nBid, featureStr);
}
//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
  //---
   
}
//+------------------------------------------------------------------+
//| Tester function                                                  |
//+------------------------------------------------------------------+
double OnTester()
{
  //---
  double ret=0.0;
  //---

  //---
  return(ret);
}
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                   BitPattern.mq4 |
//|                                   Copyright 2022, Hiroshi Manabe |
//|                                                                  |
//+------------------------------------------------------------------+
#property strict

uint curIndex = 0;
uint priceList[10000];
uint timeList[10000];
uint timeWidths[] = {20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30};
uint timeScale = 10000;
uint bitWidth = 6;
uint bitHeight = 8;
uint byteCount = 6;
uint checkInterval = 30000;
double minProfit = 0.005;

struct OrderInfo {
  int tickets[100];
  uint time;
  uint prevChecked;
  double prevPrice;
  bool isSell;
};

OrderInfo order;

struct Feature {
  bool isSell;
  uint minWidth;
  uint maxWidth;
  uint minHeight;
  uint maxHeight;
  string bitPatternStr;
  string origStr;
};

Feature features[] = {
  {1, 22, 24, 28, 28, "606060603038", "-22-24:28-28:606060603038"},
  {1, 27, 29, 25, 26, "606070303818", "-27-29:25-26:606070303818"},
  {0, 23, 25, 24, 26, "03030303030e", "+23-25:24-26:03030303030e"},
  {0, 22, 24, 20, 22, "06030303071c", "+22-24:20-22:06030303071c"}
};

int handle_order;
bool orderOnceForDebug = false;

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

  handle_order = FileOpen("order_" + current_time_str + ".csv", FILE_WRITE | FILE_CSV);   

  //---
  return(INIT_SUCCEEDED);
}
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
  //--- destroy timer
  FileClose(handle_order);   
}
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
  int nAsk = (int)(Ask * 1000);
  priceList[curIndex] = nAsk;
  uint curTime = GetTickCount();
  timeList[curIndex] = curTime;
  uint bufSize = ArraySize(priceList);
  uint c = curIndex;
  curIndex = (curIndex + 1) % bufSize;
  bool spreadIsWide = Ask > Bid + 0.009;
  if (order.tickets[0] && !spreadIsWide) {
    bool closeFlag = false;
    if (curTime > order.time + order.prevChecked + checkInterval) {
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
        if (order.tickets[i] == 0) {
          break;
        }
        if (OrderSelect(order.tickets[i], SELECT_BY_TICKET)) {
          if (OrderCloseTime() == 0) {
            bool ret = OrderClose(
                                  OrderTicket(),
                                  OrderLots(),
                                  OrderType() == OP_BUY ? Bid : Ask,
                                  10,
                                  clrWhite);
            if (ret == false) {
              Print("オーダークローズエラー：エラーコード=", GetLastError());
            }
          }
          if (OrderCloseTime()) {
            Print("オーダークローズ、利益：", OrderProfit());
            FileWrite(handle_order, "Order close, time:" + IntegerToString(GetTickCount()) + 
                      " profit: " + DoubleToStr(OrderProfit()));
            order.tickets[i] = 0;
          }
        }
      }
    }
    if (order.tickets[0]) {
      return;
    }
  }
  for (uint i = 0; i < ArraySize(timeWidths); ++i) {
    uint startTime = curTime - timeWidths[i] * timeScale + 1;
    int minRelPrice = 0;
    int maxRelPrice = 0;
    uchar bits[1024] = { 0 };
    uint j = c;
    bool isOk = true;
    
    while (1) {
      if (timeList[j] && timeList[j] < startTime) {
        break;
      }
      if (priceList[j] == 0 || timeList[j] > curTime) {
        isOk = 0;
        break;
      }
      int relPrice = priceList[j] - nAsk;
      if (relPrice < minRelPrice) {
        minRelPrice = relPrice;
      }
      else if (relPrice > maxRelPrice) {
        maxRelPrice = relPrice;
      }
      j = (j + bufSize - 1) % bufSize;
    }
    
    if (!isOk && !orderOnceForDebug) {
      continue;
    }
    
    int maxRelPriceBits = bitHeight / 2 - 1;
    int minRelPriceBits = -(bitHeight / 2);
    int priceFactorMin = (-minRelPrice + -minRelPriceBits - 1) / -minRelPriceBits;
    int priceFactorMax = (maxRelPrice + maxRelPriceBits - 1) / maxRelPriceBits;
    int priceFactor = 1;
    
    if (priceFactorMin > priceFactor) {
      priceFactor = priceFactorMin;
    }
    
    if (priceFactorMax > priceFactor) {
      priceFactor = priceFactorMax;
    }
    
    uint minPrice = nAsk + (minRelPriceBits * priceFactor);

    j = c;
    while (1) {
      if (timeList[j] < startTime) {
        break;
      }
      uint time = timeList[j];
      uint price = priceList[j];
      int timeDiff = time - startTime;
      int priceDiff = price - minPrice;
      int timeIndex = timeDiff / (timeWidths[i] * timeScale / bitWidth);
      int priceIndex = priceDiff / priceFactor;
      int bitPos = priceIndex + timeIndex * bitHeight;
      int byteIndex = bitPos >> 3;
      int bitData = 1 << (bitPos % 8);
      if (priceDiff >= 0 && priceIndex < bitHeight) {
        bits[byteIndex] |= bitData;
      }
      j = (j + bufSize - 1) % bufSize;
    }
    string bitPatternStr = "";
    for (uint k = 0; k < (uint)byteCount; ++k) {
      bitPatternStr += StringFormat("%02x", bits[k]);
    }
    for (uint k = 0; k < (uint)ArraySize(features); ++k) {
      Feature f = features[k];
      double lossCutWidth = 0.05;
      if (orderOnceForDebug || order.tickets[0] == 0 &&
          timeWidths[i] >= f.minWidth &&
          timeWidths[i] <= f.maxWidth &&
          priceFactor >= f.minHeight &&
          priceFactor <= f.maxHeight &&
          bitPatternStr == f.bitPatternStr) {
        orderOnceForDebug = false;
        
        int handle_signal = FileOpen("signal.csv", FILE_WRITE | FILE_CSV | FILE_COMMON);
        FileWrite(handle_signal, GetTickCount() + "," +
                                 (f.isSell ? "sell" : "buy") + "," +
                                 lossCutWidth + "," +
                                 f.origStr);
        FileClose(handle_signal);
                                    
        double price = f.isSell ? Bid : Ask;
        double closePrice = f.isSell ? Ask : Bid;
        double maxBet = (double)(int(AccountInfoDouble(ACCOUNT_BALANCE) * 0.023 / price) - 1) / 100.0;
        int parts = int((maxBet + 10) / 10);
        double bet = (double)int(maxBet * 10 / parts) / 10.0;
        for (uint l = 0; l < parts; ++l) {
          int ticket = OrderSend(Symbol(),
                    f.isSell ? OP_SELL : OP_BUY,
                    bet,
                    price,
                    4,
                    f.isSell ? closePrice + lossCutWidth : closePrice - lossCutWidth,
                    0);
          if (ticket) {
            order.tickets[l] = ticket;
          }
          else {
            Print("オーダーエラー：エラーコード=", GetLastError());
          }
        }
        if (order.tickets[0]) {
          string orderStr = "Order, time: " + IntegerToString(GetTickCount()) + 
            " timeWidth: " + IntegerToString(timeWidths[i]) + 
            " scale: " + IntegerToString(priceFactor) +
            " feature: " + f.origStr + 
            " " + (f.isSell ? "sell" : "buy");
          Print(orderStr);
          FileWrite(handle_order, orderStr);
          order.time = curTime;
          order.prevChecked = 0;
          order.prevPrice = Ask;
          order.isSell = f.isSell;
        }
      }
    }
  }
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

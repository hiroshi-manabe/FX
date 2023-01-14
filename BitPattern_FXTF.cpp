//+------------------------------------------------------------------+
//|                                                   BitPattern.mq4 |
//|                                   Copyright 2022, Hiroshi Manabe |
//|                                                                  |
//+------------------------------------------------------------------+
#property strict

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
  if (Ask > Bid + 0.003) {
    return;
  }
  uint curTime = GetTickCount();
  if (order.tickets[0] && FileIsExist("signal_close.csv", FILE_COMMON)) {
    bool orderClosed = true;
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
        else {
            orderClosed = false;
        }
      }
    }
    if (orderClosed) {
      FileDelete("signal_close.csv", FILE_COMMON);
    }
  }
  if (order.tickets[0]) {
    return;
  }
  
  if (!FileIsExist("signal.csv", FILE_COMMON)) {
    return;
  }
  int handle_signal = FileOpen("signal.csv", FILE_READ | FILE_CSV | FILE_COMMON, ",");
  string s;
  s = FileReadString(handle_signal);
  long tickCount = StringToInteger(s);
  string sellStr = FileReadString(handle_signal);
  s = FileReadString(handle_signal);  
  double lossCutWidth = StringToDouble(s);
  if (lossCutWidth < 0.056) {
    lossCutWidth = 0.056;
  }
  string origStr = FileReadString(handle_signal);
  FileClose(handle_signal);
  FileDelete("signal.csv", FILE_COMMON);
  bool isSell = sellStr == "sell";
  
  if (order.tickets[0] == 0) {
    double price = isSell ? Bid : Ask;
    double closePrice = isSell ? Ask : Bid;
    double maxBet = (double)(int(AccountInfoDouble(ACCOUNT_BALANCE) * 0.023 / price) - 1) / 100.0;
    int parts = int((maxBet + 10) / 10);
    double bet = (double)int(maxBet * 10 / parts) / 10.0;
    for (uint l = 0; l < parts; ++l) {
      int ticket = OrderSend(Symbol(),
                isSell ? OP_SELL : OP_BUY,
                bet,
                price,
                4,
                isSell ? closePrice + lossCutWidth : closePrice - lossCutWidth,
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
        " feature: " + origStr + 
        " " + (isSell ? "sell" : "buy");
      Print(orderStr);
      FileWrite(handle_order, orderStr);
      order.time = curTime;
      order.prevChecked = 0;
      order.prevPrice = Ask;
      order.isSell = isSell;
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

# 前端輪詢優化說明

## 問題描述

用戶報告在調用 `/v1/sharedb/documents/sync` 之後，前端會連續請求十幾次 `/v1/sharedb/documents/7`，這會造成不必要的服務器負載和網絡流量。

## 問題分析

### 原始問題
1. **動態間隔調整**：輪詢機制會動態調整間隔，每次調整都會重啟定時器
2. **依賴項過多**：`pollForUpdates` 函數有太多依賴項，導致頻繁重建
3. **缺乏防抖**：同步操作沒有防抖機制，可能觸發連鎖反應
4. **狀態更新觸發**：狀態更新會觸發 useEffect 重新執行，造成額外請求

### 根本原因
- 同步操作後狀態變化觸發輪詢重啟
- 輪詢間隔動態調整導致定時器頻繁重建
- 缺乏請求頻率控制機制

## 優化方案

### 1. 固定輪詢間隔
```typescript
// 舊邏輯：動態調整間隔
const newInterval = isUserEditing.current ? 3000 : Math.min(pollInterval.current * 1.1, 15000);
if (newInterval !== pollInterval.current) {
  pollInterval.current = newInterval;
  // 重啟定時器...
}

// 新邏輯：固定間隔
const POLL_INTERVAL = 5000; // 固定 5 秒間隔
pollTimer.current = setInterval(() => {
  pollForUpdates();
}, POLL_INTERVAL);
```

### 2. 減少依賴項
```typescript
// 舊邏輯：過多依賴項
const pollForUpdates = useCallback(async () => {
  // ...
}, [documentId, documentState, setDocumentState, updateEditorContent, onContentChange, performSync, onCollaborativeUpdate, sharedbClient]);

// 新邏輯：最少依賴項
const pollForUpdates = useCallback(async () => {
  // ...
}, [sharedbClient]); // 只保留必要依賴
```

### 3. 添加防抖機制
```typescript
// 添加同步防抖
const now = Date.now();
if (now - lastSyncTime.current < 1000) {
  console.log('Sync too frequent, skipping');
  return false;
}
lastSyncTime.current = now;
```

### 4. 穩定的輪詢啟動
```typescript
// 舊邏輯：依賴 pollForUpdates 變化
useEffect(() => {
  pollTimer.current = setInterval(pollForUpdates, pollInterval.current);
  return () => clearInterval(pollTimer.current);
}, [pollForUpdates]); // 會頻繁重建

// 新邏輯：空依賴數組
useEffect(() => {
  const POLL_INTERVAL = 5000;
  pollTimer.current = setInterval(() => {
    pollForUpdates();
  }, POLL_INTERVAL);
  return () => clearInterval(pollTimer.current);
}, []); // 只在組件掛載時執行一次
```

## 優化效果

### 預期改進
1. **請求頻率降低**：從不規則的高頻請求變為固定 5 秒間隔
2. **資源使用優化**：減少不必要的定時器重建和網絡請求
3. **用戶體驗提升**：避免因頻繁請求導致的性能問題
4. **服務器負載減輕**：減少不必要的 API 調用

### 日誌監控
優化後可以通過以下日誌監控效果：
- `"Sync too frequent, skipping"` - 防抖生效
- `"Sync already in progress, skipping"` - 避免併發同步
- `"Starting collaborative polling with fixed interval"` - 穩定輪詢啟動
- `"Stopped collaborative polling"` - 清理輪詢定時器

## 測試建議

### 測試場景
1. **正常編輯**：輸入內容後觀察同步頻率
2. **並發操作**：快速連續輸入觀察防抖效果
3. **協作編輯**：多用戶同時編輯觀察輪詢行為
4. **頁面切換**：進入/離開編輯器觀察定時器清理

### 監控指標
- 每分鐘 ShareDB 請求次數
- 同步操作響應時間
- 瀏覽器網絡面板中的請求頻率
- 控制台日誌中的防抖/跳過記錄

## 後續優化

### 可能的進一步改進
1. **WebSocket 長連接**：替換輪詢機制為推送機制
2. **智能暫停**：頁面不可見時暫停輪詢
3. **請求合併**：批量處理多個操作
4. **緩存策略**：避免重複請求相同數據

### 版本快照優化
同時優化了版本快照創建邏輯，只有內容真正變化時才創建版本：
- 使用內容哈希比較檢測變化
- 避免創建重複的版本快照
- 減少數據庫寫入操作 
# Derived JSON5 Contract

- Source: `lib/page/home_page/home_page.dart`
- Route: `MaterialApp.home`
- Figma: `https://www.figma.com/design/8o2jFlD9xlVHQYmp2ddidb/Colorful-Stock-App---iOS-UI-Kit--Community-?node-id=14-11&t=BobLQ33X6rW4neR8-4 | Community stock app homepage adapted into a FlowR contract-first example.`

## BFF-API

### GET <BASE>/home-page/summary
- Request DTOs: [HomePortfolioSummaryReq]
- Response DTOs: [HomePortfolioSummaryModel]

#### Request JSON5

```json5
{
}
```

#### Response JSON5

```json5
{
  // Dart type: String
  headline: 'string',
  // Dart type: String
  totalAssetLabel: 'string',
  // Dart type: String
  changeRateLabel: 'string',
}
```

### GET <BASE>/home-page/recommendations
- Request DTOs: [HomeStockRecommendationReq]
- Response DTOs: [HomeStockRecommendationModel]

#### Request JSON5

```json5
{
  // Dart type: String
  // Default: 'home'
  slot: 'string',
  // Dart type: int
  // Default: 3
  limit: 0,
}
```

#### Response JSON5

```json5
{
  // Dart type: String
  symbol: 'string',
  // Dart type: String
  displayPrice: 'string',
  // Dart type: String
  gradientStartHex: 'string',
  // Dart type: String
  gradientEndHex: 'string',
}
```

### GET <BASE>/home-page/opinions
- Request DTOs: [HomeOpinionArticleReq]
- Response DTOs: [HomeOpinionArticleModel]

#### Request JSON5

```json5
{
  // Dart type: String
  // Default: 'stocks'
  topic: 'string',
  // Dart type: int
  // Default: 3
  limit: 0,
}
```

#### Response JSON5

```json5
{
  // Dart type: String
  id: 'string',
  // Dart type: String
  headline: 'string',
  // Dart type: String
  summary: 'string',
}
```

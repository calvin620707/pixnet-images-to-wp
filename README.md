# 痞客邦搬圖到WordPress

這個主要是幫助痞客邦部落客搬家到WordPress的時候，把文章裡面的圖像從痞客邦搬到WordPress上。
當你使用痞客邦匯出MT檔，然後用WordPress把MT檔讀進去的時候，所有文章的圖片其實都還是連回痞客邦的。
你可以使用這個工具自動把所有WordPress文章上的痞客邦圖片都從痞客邦下載下來，然後上傳到WordPress，接著會更新文章裡面所有痞客邦的圖片連結。

## 執行環境

你的電腦需要下面的工具:

* [Python 3](https://www.python.org/downloads/)
* [poetry](https://poetry.eustace.io/docs/#installation)

然後你需要安裝下面這個WordPress plugin讓你可以使用帳號密碼去存取WordPress.

* [JSON Basic Authentication](https://github.com/WP-API/Basic-Auth)

接著，在執行程式前，你需要提供你的WordPress網址，帳號跟密碼透過環境變數設定。

```env
WP_URL=https://your.wordpress.com
WP_USER=your@user.name
WP_PASSWORD=YourPassword
```

最後需要把Python的dependencies安裝好，透過下面的指令就可以了。

```bash
poetry install
```

這樣大致環境上就設定好了。

## 開始搬圖

接下來只要執行下面的指令應該就會開始搬圖了～

```bash
poetry shell
python move_images/app.py
```

不過要注意一下有時候可能WordPress或是痞客邦網路不穩定導致程式中斷，這時候可能需要重新執行上面的指令。
這段程式碼會記錄每個文章處理到什麼進度，所以大部分處理好的事情不會重複再處理一次。

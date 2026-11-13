package com.teleghost.app

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.View
import android.view.WindowManager
import android.webkit.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import java.io.File
import java.io.FileOutputStream
import java.util.UUID

class MainActivity : AppCompatActivity(), mobile.PlatformBridge {

    private lateinit var webView: WebView

    companion object {
        private const val TAG = "Hydra"
        private const val SERVER_URL = "http://127.0.0.1:8080"
        private const val HEALTH_URL = "$SERVER_URL/health"
        private const val MAX_RETRIES = 30
        private const val RETRY_DELAY_MS = 1000L
        private const val NOTIFICATION_CHANNEL_ID = "teleghost_messages"
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "Messages"
            val descriptionText = "New messages from contacts"
            val importance = android.app.NotificationManager.IMPORTANCE_DEFAULT
            val channel = android.app.NotificationChannel(NOTIFICATION_CHANNEL_ID, name, importance).apply {
                description = descriptionText
            }
            val notificationManager: android.app.NotificationManager =
                getSystemService(android.content.Context.NOTIFICATION_SERVICE) as android.app.NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val uri = result.data?.data
            if (uri != null) {
                Thread {
                    try {
                        val path = copyFileToInternalStorage(uri)
                        mobile.Mobile.onFileSelected(path)
                    } catch (e: Exception) {
                        android.util.Log.e(TAG, "Failed to copy file", e)
                        mobile.Mobile.onFileSelected("")
                    }
                }.start()
            } else {
                mobile.Mobile.onFileSelected("")
            }
        } else {
            mobile.Mobile.onFileSelected("")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        window.decorView.systemUiVisibility = (
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
        )
        window.statusBarColor = android.graphics.Color.TRANSPARENT
        window.navigationBarColor = android.graphics.Color.parseColor("#121212")

        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)

        webView = WebView(this).apply {
            layoutParams = android.view.ViewGroup.LayoutParams(
                android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                android.view.ViewGroup.LayoutParams.MATCH_PARENT
            )
            setBackgroundColor(android.graphics.Color.parseColor("#121212"))
        }
        setContentView(webView)

        setupWebView()
        startGoService()
        createNotificationChannel()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val needed = mutableListOf<String>()
            if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                needed.add(android.Manifest.permission.RECORD_AUDIO)
            }
            if (checkSelfPermission(android.Manifest.permission.CAMERA) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                needed.add(android.Manifest.permission.CAMERA)
            }
            if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                needed.add(android.Manifest.permission.POST_NOTIFICATIONS)
            }
            if (needed.isNotEmpty()) {
                requestPermissions(needed.toTypedArray(), 101)
            }
        }

        mobile.Mobile.setPlatformBridge(this)
    }

    fun openFile(path: String) {
        runOnUiThread {
            try {
                val file = File(path)
                if (!file.exists()) {
                    android.widget.Toast.makeText(this, "File not found: $path", android.widget.Toast.LENGTH_SHORT).show()
                    return@runOnUiThread
                }
                val uri = androidx.core.content.FileProvider.getUriForFile(
                    this,
                    "com.teleghost.app.fileprovider",
                    file
                )
                val intent = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, getMimeType(path))
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                startActivity(Intent.createChooser(intent, "Open File"))
            } catch (e: Exception) {
                android.util.Log.e(TAG, "Failed to open file", e)
            }
        }
    }

    private fun getMimeType(url: String): String {
        var type: String? = null
        val extension = MimeTypeMap.getFileExtensionFromUrl(url)
        if (extension != null) {
            type = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension)
        }
        return type ?: "*/*"
    }

    override fun pickFile() {
        runOnUiThread {
            try {
                val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                    type = "*/*"
                    addCategory(Intent.CATEGORY_OPENABLE)
                    putExtra(Intent.EXTRA_MIME_TYPES, arrayOf("image/*", "video/*", "application/pdf", "text/*", "application/zip"))
                }
                filePickerLauncher.launch(intent)
            } catch (e: Exception) {
                mobile.Mobile.onFileSelected("")
            }
        }
    }

    override fun shareFile(path: String) {
        runOnUiThread {
            try {
                val file = File(path)
                if (!file.exists()) return@runOnUiThread
                val uri = androidx.core.content.FileProvider.getUriForFile(
                    this,
                    "com.teleghost.app.fileprovider",
                    file
                )
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "application/zip"
                    putExtra(Intent.EXTRA_STREAM, uri)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                startActivity(Intent.createChooser(intent, "Share Hydra Backup"))
            } catch (e: Exception) {
                android.util.Log.e(TAG, "Failed to share file", e)
            }
        }
    }

    override fun clipboardSet(text: String) {
        runOnUiThread {
            try {
                val clipboard = getSystemService(android.content.Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
                val clip = android.content.ClipData.newPlainText("Hydra", text)
                clipboard.setPrimaryClip(clip)
            } catch (e: Exception) {
                android.util.Log.e(TAG, "Clipboard set failed", e)
            }
        }
    }

    override fun showNotification(title: String, message: String) {
        runOnUiThread {
            try {
                val builder = androidx.core.app.NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
                    .setSmallIcon(R.mipmap.ic_launcher)
                    .setContentTitle(title)
                    .setContentText(message)
                    .setPriority(androidx.core.app.NotificationCompat.PRIORITY_DEFAULT)
                    .setAutoCancel(true)
                    .setOngoing(false)

                val intent = Intent(this, MainActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                }
                val pendingIntent: android.app.PendingIntent = android.app.PendingIntent.getActivity(this, 0, intent, android.app.PendingIntent.FLAG_IMMUTABLE)
                builder.setContentIntent(pendingIntent)

                with(androidx.core.app.NotificationManagerCompat.from(this)) {
                    notify(System.currentTimeMillis().toInt(), builder.build())
                }
            } catch (e: Exception) {
                android.util.Log.e(TAG, "Notification failed", e)
            }
        }
    }

    override fun saveFile(path: String, filename: String) {
        runOnUiThread {
            try {
                val file = File(path)
                if (!file.exists()) return@runOnUiThread
                val contentValues = android.content.ContentValues().apply {
                    put(android.provider.MediaStore.MediaColumns.DISPLAY_NAME, filename)
                    val mime = try {
                        val ext = MimeTypeMap.getFileExtensionFromUrl(filename)
                        MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext) ?: "application/octet-stream"
                    } catch(e: Exception) { "application/octet-stream" }
                    put(android.provider.MediaStore.MediaColumns.MIME_TYPE, mime)
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        put(android.provider.MediaStore.MediaColumns.RELATIVE_PATH, android.os.Environment.DIRECTORY_DOWNLOADS)
                        put(android.provider.MediaStore.MediaColumns.IS_PENDING, 1)
                    }
                }
                val resolver = applicationContext.contentResolver
                val uri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    resolver.insert(android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI, contentValues)
                } else {
                    resolver.insert(android.provider.MediaStore.Files.getContentUri("external"), contentValues)
                }
                if (uri != null) {
                    resolver.openOutputStream(uri)?.use { output ->
                        java.io.FileInputStream(file).use { input ->
                            input.copyTo(output)
                        }
                    }
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        contentValues.clear()
                        contentValues.put(android.provider.MediaStore.MediaColumns.IS_PENDING, 0)
                        resolver.update(uri, contentValues, null, null)
                    }
                    android.widget.Toast.makeText(this, "Сохранено в Загрузки", android.widget.Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                android.util.Log.e(TAG, "Save file failed", e)
            }
        }
    }

    private fun copyFileToInternalStorage(uri: Uri): String {
        val contentResolver = applicationContext.contentResolver
        val mimeType = contentResolver.getType(uri) ?: "application/octet-stream"
        val ext = MimeTypeMap.getSingleton().getExtensionFromMimeType(mimeType) ?: "bin"
        val filename = "upload_${UUID.randomUUID()}.$ext"
        val tempDir = File(filesDir, "tmp_uploads")
        if (!tempDir.exists()) tempDir.mkdirs()
        val destFile = File(tempDir, filename)
        contentResolver.openInputStream(uri)?.use { input ->
            FileOutputStream(destFile).use { output ->
                input.copyTo(output)
            }
        } ?: throw Exception("Cannot open input stream")
        return destFile.absolutePath
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            cacheMode = WebSettings.LOAD_DEFAULT
            mediaPlaybackRequiresUserGesture = false
            useWideViewPort = true
            loadWithOverviewMode = true
            setSupportZoom(false)
            builtInZoomControls = false
            displayZoomControls = false
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(
                view: WebView?,
                request: WebResourceRequest?
            ): Boolean {
                val url = request?.url?.toString() ?: return false
                if (url.startsWith(SERVER_URL)) return false
                startActivity(Intent(Intent.ACTION_VIEW, request?.url))
                return true
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                if (request?.isForMainFrame == true) {
                    view?.postDelayed({ waitForServerAndLoad() }, RETRY_DELAY_MS)
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest?) {
                runOnUiThread {
                    request?.grant(request.resources)
                }
            }

            override fun onConsoleMessage(msg: ConsoleMessage?): Boolean {
                android.util.Log.d(TAG, "JS: ${msg?.message()} [${msg?.sourceId()}:${msg?.lineNumber()}]")
                return true
            }
        }
    }

    private fun startGoService() {
        val intent = Intent(this, TeleGhostService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
        waitForServerAndLoad()
    }

    private fun waitForServerAndLoad(retryCount: Int = 0) {
        if (retryCount >= MAX_RETRIES) {
            runOnUiThread {
                webView.loadData(
                    "<html><body style='background:#121212;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;'><div style='text-align:center;'><h2>⚠️ Не удалось запустить сервер</h2><p>Попробуйте перезапустить приложение</p></div></body></html>",
                    "text/html", "UTF-8"
                )
            }
            return
        }

        Thread {
            try {
                val url = java.net.URL(HEALTH_URL)
                val connection = url.openConnection() as java.net.HttpURLConnection
                connection.connectTimeout = 1000
                connection.readTimeout = 1000
                connection.requestMethod = "GET"
                val responseCode = connection.responseCode
                connection.disconnect()
                if (responseCode == 200) {
                    runOnUiThread {
                        webView.loadUrl(SERVER_URL)
                    }
                    return@Thread
                }
            } catch (e: Exception) {
                android.util.Log.d(TAG, "Health check failed: ${e.message}")
            }
            runOnUiThread {
                webView.postDelayed({ waitForServerAndLoad(retryCount + 1) }, RETRY_DELAY_MS)
            }
        }.start()
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            moveTaskToBack(true)
        }
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
        mobile.Mobile.setPlatformBridge(this)
    }

    override fun onPause() {
        webView.onPause()
        super.onPause()
    }
}

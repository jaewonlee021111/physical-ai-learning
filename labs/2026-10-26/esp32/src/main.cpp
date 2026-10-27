#include <Arduino.h>
#include <WiFi.h>
#include "camera_pins.h"
#if __has_include("wifi_config.h")
#include "wifi_config.h"
#else
#include "wifi_config.example.h"
#endif
static String wifiName = WIFI_SSID;
static String wifiPassword = WIFI_PASSWORD;
static String serialLine;
static uint32_t reconnectAt = 0;

/// <summary>주변 Wi-Fi를 검색한다. 출력은 로컬 시리얼에만 남긴다.</summary>
static void scanWifi()
{
    int count = WiFi.scanNetworks();
    Serial.println("# / SSID / RSSI dBm / channel / authentication");
    for (int i = 0; i < count; i++)
    {
        Serial.printf("%d / %s / %d / %d / %d\n", i, WiFi.SSID(i).c_str(), WiFi.RSSI(i), WiFi.channel(i), WiFi.encryptionType(i));
    }
    Serial.println("CONNECT <network-number> <password>, or SCAN. Password is never echoed.");
}

/// <summary>선택한 Wi-Fi에 연결하고 성공·실패를 구분해 출력한다.</summary>
static bool connectWifi()
{
    if (wifiName.isEmpty())
    {
        return false;
    }
    WiFi.begin(wifiName.c_str(), wifiPassword.c_str());
    uint32_t start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 15000)
    {
        delay(100);
    }
    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.printf("CONNECTED IP=%s RSSI=%d\n", WiFi.localIP().toString().c_str(), WiFi.RSSI());
        Serial.printf("STREAM http://%s/stream\n", WiFi.localIP().toString().c_str());
        return true;
    }
    Serial.println("Wi-Fi connection timed out. Check 2.4 GHz, SSID, password and isolation.");
    return false;
}

/// <summary>시리얼 입력으로 네트워크를 고르고 끊어진 연결을 재시도한다.</summary>
static void pollWifi()
{
    while (Serial.available())
    {
        char character = Serial.read();
        if (character == '\n')
        {
            serialLine.trim();
            if (serialLine == "SCAN")
            {
                scanWifi();
            }
            else if (serialLine.startsWith("CONNECT "))
            {
                int split = serialLine.indexOf(' ', 8);
                String number = split < 0 ? serialLine.substring(8) : serialLine.substring(8, split);
                int index = number.toInt();
                bool numeric = !number.isEmpty();
                for (unsigned int i = 0; i < number.length(); i++)
                {
                    numeric = numeric && isDigit(number[i]);
                }
                if (numeric && index >= 0 && index < WiFi.scanComplete())
                {
                    wifiName = WiFi.SSID(index);
                    wifiPassword = split < 0 ? "" : serialLine.substring(split + 1);
                    connectWifi();
                }
                else
                {
                    Serial.println("Invalid network number. Run SCAN first.");
                }
            }
            serialLine = "";
        }
        else if (character != '\r' && serialLine.length() < 256)
        {
            serialLine += character;
        }
    }
    if (!wifiName.isEmpty() && WiFi.status() != WL_CONNECTED && millis() - reconnectAt >= 10000)
    {
        reconnectAt = millis();
        WiFi.reconnect();
    }
}

/// <summary>STA와 절전 설정을 준비하고 초기 접속을 시도한다.</summary>
static void setupWifi()
{
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    scanWifi();
    connectWifi();
}

// httpd 서버는 스트림 요청 하나가 처리 루프를 점유한다. /stream 동시 시청자는 1명.
// Python 게이트웨이 한 개만 ESP32 스트림을 읽고 여러 브라우저에 재배포한다.
#include <esp_camera.h>
#include <esp_http_server.h>
#include <img_converters.h>
#include <freertos/semphr.h>

static httpd_handle_t streamServer = nullptr;
static httpd_handle_t statusServer = nullptr;
static SemaphoreHandle_t frameMutex;
static bool cameraReady = false;
static portMUX_TYPE statsMutex = portMUX_INITIALIZER_UNLOCKED;
struct CameraStats
{
    uint32_t frames = 0;
    uint32_t bytes = 0;
    int clients = 0;
    float fps = 0;
    float kbPerFrame = 0;
};
static CameraStats cameraStats;

/// <summary>다른 태스크와 공유하는 전송 통계를 복사한다.</summary>
static CameraStats snapshotStats()
{
    portENTER_CRITICAL(&statsMutex);
    CameraStats snapshot = cameraStats;
    portEXIT_CRITICAL(&statsMutex);
    return snapshot;
}

/// <summary>공식 XIAO Sense 핀으로 카메라를 초기화한다. SD 카드는 사용하지 않는다.</summary>
static bool initializeCamera()
{
    camera_config_t config = {};
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = CAM_D0;
    config.pin_d1 = CAM_D1;
    config.pin_d2 = CAM_D2;
    config.pin_d3 = CAM_D3;
    config.pin_d4 = CAM_D4;
    config.pin_d5 = CAM_D5;
    config.pin_d6 = CAM_D6;
    config.pin_d7 = CAM_D7;
    config.pin_xclk = CAM_XCLK;
    config.pin_pclk = CAM_PCLK;
    config.pin_vsync = CAM_VSYNC;
    config.pin_href = CAM_HREF;
    config.pin_sccb_sda = CAM_SDA;
    config.pin_sccb_scl = CAM_SCL;
    config.pin_pwdn = CAM_PWDN;
    config.pin_reset = CAM_RESET;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.grab_mode = CAMERA_GRAB_LATEST;
    config.jpeg_quality = CAMERA_JPEG_QUALITY;
    if (psramFound())
    {
        config.frame_size = CAMERA_FRAME_SIZE;
        config.fb_count = 2;
        config.fb_location = CAMERA_FB_IN_PSRAM;
    }
    else
    {
        config.frame_size = FRAMESIZE_QVGA;
        config.fb_count = 1;
        config.fb_location = CAMERA_FB_IN_DRAM;
        Serial.println("No PSRAM: QVGA, DRAM, one framebuffer fallback.");
    }
    esp_err_t error = esp_camera_init(&config);
    Serial.printf("Camera init: 0x%x / PSRAM=%u bytes\n", error, static_cast<unsigned int>(ESP.getPsramSize()));
    return error == ESP_OK;
}

/// <summary>홈페이지에는 안내와 링크만 제공하여 스트림을 중복 점유하지 않는다.</summary>
static esp_err_t homeHandler(httpd_req_t *request)
{
    httpd_resp_set_type(request, "text/html; charset=utf-8");
    return httpd_resp_sendstr(request, "<h1>XIAO Camera</h1><p>One upstream viewer only.</p><a href='/stream'>MJPEG stream</a><p>Status and capture: port 81.</p>");
}

/// <summary>상태 조회는 별도 포트에서 스트림과 동시에 처리한다.</summary>
static esp_err_t statusHandler(httpd_req_t *request)
{
    CameraStats stats = snapshotStats();
    String json = String("{\"ip\":\"") + WiFi.localIP().toString() + "\",\"rssi\":" + WiFi.RSSI() +
        ",\"uptime\":" + millis() / 1000 + ",\"psram\":" + ESP.getPsramSize() +
        ",\"frame_size\":\"" + (psramFound() ? "VGA" : "QVGA") + "\",\"fps\":" + String(stats.fps, 2) +
        ",\"clients\":" + stats.clients + "}";
    httpd_resp_set_type(request, "application/json");
    return httpd_resp_sendstr(request, json.c_str());
}

/// <summary>JPEG 프레임을 전송하고 변환 버퍼와 카메라 버퍼를 반드시 반환한다.</summary>
static esp_err_t sendFrame(httpd_req_t *request, bool multipart)
{
    if (xSemaphoreTake(frameMutex, pdMS_TO_TICKS(3000)) != pdTRUE)
    {
        return ESP_FAIL;
    }
    camera_fb_t *frame = esp_camera_fb_get();
    if (frame == nullptr)
    {
        xSemaphoreGive(frameMutex);
        return ESP_FAIL;
    }
    uint8_t *jpeg = frame->buf;
    size_t length = frame->len;
    bool converted = frame->format != PIXFORMAT_JPEG;
    bool valid = !converted || frame2jpg(frame, 80, &jpeg, &length);
    esp_err_t result = ESP_FAIL;
    if (valid)
    {
        if (multipart)
        {
            char header[160];
            int size = snprintf(header, sizeof(header), "\r\n--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\nX-Timestamp: %lu\r\n\r\n", static_cast<unsigned int>(length), static_cast<unsigned long>(millis()));
            result = httpd_resp_send_chunk(request, header, size);
            if (result == ESP_OK)
            {
                result = httpd_resp_send_chunk(request, reinterpret_cast<char *>(jpeg), length);
            }
        }
        else
        {
            httpd_resp_set_type(request, "image/jpeg");
            result = httpd_resp_send(request, reinterpret_cast<char *>(jpeg), length);
        }
        if (result == ESP_OK && multipart)
        {
            portENTER_CRITICAL(&statsMutex);
            cameraStats.frames++;
            cameraStats.bytes += length;
            portEXIT_CRITICAL(&statsMutex);
        }
    }
    if (converted && valid)
    {
        free(jpeg);
    }
    esp_camera_fb_return(frame);
    xSemaphoreGive(frameMutex);
    return result;
}

/// <summary>브라우저 또는 게이트웨이 한 곳에 연속 JPEG를 보낸다.</summary>
static esp_err_t streamHandler(httpd_req_t *request)
{
    httpd_resp_set_type(request, "multipart/x-mixed-replace; boundary=frame");
    portENTER_CRITICAL(&statsMutex);
    cameraStats.clients = 1;
    portEXIT_CRITICAL(&statsMutex);
    while (WiFi.status() == WL_CONNECTED && sendFrame(request, true) == ESP_OK)
    {
        vTaskDelay(pdMS_TO_TICKS(10));
    }
    portENTER_CRITICAL(&statsMutex);
    cameraStats.clients = 0;
    portEXIT_CRITICAL(&statsMutex);
    return ESP_FAIL;
}

/// <summary>별도 HTTP 서버에서 사진 한 장을 보낸다.</summary>
static esp_err_t captureHandler(httpd_req_t *request)
{
    return sendFrame(request, false);
}

/// <summary>경로 핸들러를 등록한다.</summary>
static void addRoute(httpd_handle_t server, const char *uri, esp_err_t (*handler)(httpd_req_t *))
{
    httpd_uri_t route = {};
    route.uri = uri;
    route.method = HTTP_GET;
    route.handler = handler;
    ESP_ERROR_CHECK(httpd_register_uri_handler(server, &route));
}

/// <summary>포트 80·81과 서로 다른 제어 포트를 사용한다.</summary>
static bool startCameraServers()
{
    httpd_config_t stream = HTTPD_DEFAULT_CONFIG();
    stream.server_port = 80;
    stream.ctrl_port = 32768;
    stream.stack_size = 8192;
    if (httpd_start(&streamServer, &stream) != ESP_OK)
    {
        return false;
    }
    addRoute(streamServer, "/", homeHandler);
    addRoute(streamServer, "/stream", streamHandler);
    httpd_config_t status = HTTPD_DEFAULT_CONFIG();
    status.server_port = 81;
    status.ctrl_port = 32769;
    status.stack_size = 8192;
    if (httpd_start(&statusServer, &status) != ESP_OK)
    {
        httpd_stop(streamServer);
        streamServer = nullptr;
        return false;
    }
    addRoute(statusServer, "/status", statusHandler);
    addRoute(statusServer, "/capture", captureHandler);
    return true;
}

/// <summary>카메라와 네트워크를 준비한다. Wi-Fi CLI 연결 후에 서버를 시작한다.</summary>
void setup()
{
    Serial.begin(115200);
    uint32_t serialAt=millis();
    while (!Serial && millis()-serialAt<3000)
    {
        delay(10);
    }
    frameMutex = xSemaphoreCreateMutex();
    cameraReady = frameMutex != nullptr && initializeCamera();
    if (!cameraReady)
    {
        Serial.println("Camera init failed: restarting in 5s");
        delay(5000);
        ESP.restart();
    }
    setupWifi();
    Serial.println("/stream supports one upstream viewer. Close direct ESP32 browser tabs when using Python.");
}
/// <summary>연결 복구와 5초 단위 전송 통계를 처리한다.</summary>
void loop()
{
    pollWifi();
    if (cameraReady && WiFi.status() == WL_CONNECTED && streamServer == nullptr)
    {
        if (startCameraServers())
        {
            Serial.printf("Stream http://%s/stream | status http://%s:81/status | capture http://%s:81/capture\n",WiFi.localIP().toString().c_str(),WiFi.localIP().toString().c_str(),WiFi.localIP().toString().c_str());
        }
    }
    static uint32_t lastTime = 0;
    static uint32_t lastFrames = 0;
    static uint32_t lastBytes = 0;
    if (millis() - lastTime >= 5000)
    {
        CameraStats stats = snapshotStats();
        uint32_t count = stats.frames - lastFrames;
        float fps = count * 1000.0f / (millis() - lastTime);
        float size = count == 0 ? 0 : (stats.bytes - lastBytes) / (1024.0f * count);
        portENTER_CRITICAL(&statsMutex);
        cameraStats.fps = fps;
        cameraStats.kbPerFrame = size;
        portEXIT_CRITICAL(&statsMutex);
        Serial.printf("FPS=%.2f KB/frame=%.2f clients=%d RSSI=%d\n", fps, size, stats.clients, WiFi.RSSI());
        lastTime = millis();
        lastFrames = stats.frames;
        lastBytes = stats.bytes;
    }
    delay(10);
}

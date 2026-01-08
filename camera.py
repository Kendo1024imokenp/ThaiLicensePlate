import cv2
import time
import requests

API_URL = "https://api.aiforthai.in.th/lpr-v2"
API_KEY = "3TkFIXOflVelRiBSgg4JLM8DF4AzLn59"

SCAN_INTERVAL = 2.0  # seconds

plates = []       # array to store detected plates
plates_seen = set()

def call_lpr_api(jpg_bytes):
    headers = {"apikey": API_KEY}
    files = {"image": ("frame.jpg", jpg_bytes, "image/jpeg")}
    data = {"crop": "0", "rotate": "0"}

    try:
        r = requests.post(API_URL, headers=headers, files=files, data=data, timeout=15)
        if r.status_code != 200:
            print("HTTP error:", r.status_code)
            return None

        return r.json()
    except Exception as e:
        print("API error:", e)
        return None


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open camera")
        return

    print("Camera started. Scanning every 2 seconds.")
    print("Press Q to quit.")

    last_scan_time = 0.0
    last_detected = []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera read failed")
            break

        now = time.time()

        # -------- AUTOMATIC SCAN EVERY 2 SECONDS --------
        if now - last_scan_time >= SCAN_INTERVAL:
            last_scan_time = now

            ok, jpg = cv2.imencode(".jpg", frame)
            if ok:
                result = call_lpr_api(jpg.tobytes())
            else:
                result = None

            last_detected = []

            if isinstance(result, list):
                for det in result:
                    plate = det.get("lpr", "").strip()
                    if plate:
                        last_detected.append(plate)

                        if plate not in plates_seen:
                            plates_seen.add(plate)
                            plates.append(plate)
                            print("NEW PLATE:", plate)

            # If nothing detected, it just silently continues
            if not last_detected:
                print("No plate detected this cycle.")

        # -------- DISPLAY --------
        overlay = [
            f"Last scan: {int(now - last_scan_time)}s ago",
            f"Detected: {', '.join(last_detected) if last_detected else '-'}",
            f"Stored: {len(plates)} plates",
            "Press Q to quit"
        ]

        y = 30
        for line in overlay:
            cv2.putText(frame, line, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y += 30

        cv2.imshow("Thai LPR - Auto Scan", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    print("\nFinal plate array:")
    print(plates)


if __name__ == "__main__":
    main()

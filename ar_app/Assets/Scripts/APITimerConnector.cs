using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections;

public class APITimerConnector : MonoBehaviour
{
    public Text timerText;
    private string apiBaseUrl = "http://localhost:5000";

    void Start()
    {
        if (timerText == null)
        {
            Debug.LogError("Timer Text UI element is not assigned.");
            return;
        }
        StartCoroutine(UpdateTimer());
    }

    IEnumerator UpdateTimer()
    {
        while (true)
        {
            using (UnityWebRequest www = UnityWebRequest.Get(apiBaseUrl + "/timer"))
            {
                yield return www.SendWebRequest();

                if (www.result == UnityWebRequest.Result.Success)
                {
                    TimerStatus status = JsonUtility.FromJson<TimerStatus>(www.downloadHandler.text);

                    // Format the time into minutes and seconds
                    int minutes = status.time_remaining / 60;
                    int seconds = status.time_remaining % 60;
                    timerText.text = string.Format("{0:00}:{1:00}", minutes, seconds);
                }
                else
                {
                    Debug.LogError("Error fetching timer: " + www.error);
                    timerText.text = "--:--";
                }
            }

            yield return new WaitForSeconds(1f); // Refresh every second
        }
    }
}

[System.Serializable]
public class TimerStatus
{
    public int time_remaining;
}

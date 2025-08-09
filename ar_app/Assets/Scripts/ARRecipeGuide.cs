using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections;

public class ARRecipeGuide : MonoBehaviour
{
    public Text stepText;
    public Text timerText;
    public Text nutritionText;

    private string apiBaseUrl = "http://localhost:5000";

    void Start()
    {
        StartCoroutine(UpdateRecipeStatus());
    }

    IEnumerator UpdateRecipeStatus()
    {
        while (true)
        {
            // First, get the current step and ingredient
            using (UnityWebRequest statusRequest = UnityWebRequest.Get(apiBaseUrl + "/current_status"))
            {
                yield return statusRequest.SendWebRequest();

                if (statusRequest.result == UnityWebRequest.Result.Success)
                {
                    RecipeStatus status = JsonUtility.FromJson<RecipeStatus>(statusRequest.downloadHandler.text);
                    stepText.text = "Step: " + status.step;
                    timerText.text = "Time Left: " + status.time_remaining + "s";

                    // If we have a valid ingredient, fetch its nutrition info
                    if (!string.IsNullOrEmpty(status.ingredient))
                    {
                        // Using a coroutine to handle the second web request
                        yield return StartCoroutine(FetchNutritionInfo(status.ingredient));
                    }
                    else
                    {
                        nutritionText.text = "Nutrition: N/A";
                    }
                }
                else
                {
                    Debug.LogError("Error fetching status: " + statusRequest.error);
                    stepText.text = "Step: Error";
                    timerText.text = "Time Left: N/A";
                    nutritionText.text = "Nutrition: N/A";
                }
            }

            yield return new WaitForSeconds(2f); // Refresh every 2 seconds
        }
    }

    IEnumerator FetchNutritionInfo(string ingredient)
    {
        string encodedIngredient = UnityWebRequest.EscapeURL(ingredient);
        using (UnityWebRequest nutritionRequest = UnityWebRequest.Get(apiBaseUrl + "/nutrition?ingredient=" + encodedIngredient))
        {
            yield return nutritionRequest.SendWebRequest();

            if (nutritionRequest.result == UnityWebRequest.Result.Success)
            {
                NutritionData nutritionData = JsonUtility.FromJson<NutritionData>(nutritionRequest.downloadHandler.text);
                nutritionText.text = "Nutrition: " + nutritionData.nutrition_info;
            }
            else
            {
                Debug.LogError("Error fetching nutrition data: " + nutritionRequest.error);
                nutritionText.text = "Nutrition: Error";
            }
        }
    }
}

[System.Serializable]
public class RecipeStatus
{
    public string step;
    public int time_remaining;
    public string ingredient;
}

[System.Serializable]
public class NutritionData
{
    public string nutrition_info;
}

using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections;

public class ARRecipeGuide : MonoBehaviour
{
    [Header("Status Display")]
    public Text stepText;
    public Text timerText;
    public Text nutritionText;

    [Header("Ingredient List")]
    public Transform ingredientListContent;
    public GameObject ingredientItemPrefab;

    [Header("Nutrition Panel")]
    public GameObject nutritionPanel;
    public Text nutritionPanelText;
    public Button closeNutritionPanelButton;

    private string apiBaseUrl = "http://localhost:5000";

    void Start()
    {
        StartCoroutine(UpdateRecipeStatus());
        StartCoroutine(FetchRecipeData());

        if (closeNutritionPanelButton != null)
        {
            closeNutritionPanelButton.onClick.AddListener(() => nutritionPanel.SetActive(false));
        }
        if (nutritionPanel != null)
        {
            nutritionPanel.SetActive(false);
        }
    }

    public void OnIngredientTapped(string ingredient)
    {
        StartCoroutine(FetchAndShowNutritionPanel(ingredient));
    }

    IEnumerator FetchAndShowNutritionPanel(string ingredient)
    {
        // Show a loading message in the panel while fetching data
        nutritionPanelText.text = "Fetching nutrition info for " + ingredient + "...";
        nutritionPanel.SetActive(true);

        string encodedIngredient = UnityWebRequest.EscapeURL(ingredient);
        using (UnityWebRequest nutritionRequest = UnityWebRequest.Get(apiBaseUrl + "/nutrition?ingredient=" + encodedIngredient))
        {
            yield return nutritionRequest.SendWebRequest();

            if (nutritionRequest.result == UnityWebRequest.Result.Success)
            {
                NutritionData nutritionData = JsonUtility.FromJson<NutritionData>(nutritionRequest.downloadHandler.text);
                nutritionPanelText.text = nutritionData.nutrition_info;
            }
            else
            {
                Debug.LogError("Error fetching nutrition data for panel: " + nutritionRequest.error);
                nutritionPanelText.text = "Could not fetch nutrition info for " + ingredient + ". Please try again.";
            }
        }
    }

    void PopulateIngredientList(string[] ingredients)
    {
        // Clear existing ingredient items before populating
        foreach (Transform child in ingredientListContent)
        {
            Destroy(child.gameObject);
        }

        // Instantiate a new item for each ingredient
        foreach (string ingredient in ingredients)
        {
            GameObject itemGO = Instantiate(ingredientItemPrefab, ingredientListContent);

            Text itemText = itemGO.GetComponentInChildren<Text>();
            if (itemText != null)
            {
                itemText.text = ingredient;
            }

            Button itemButton = itemGO.GetComponent<Button>();
            if (itemButton != null)
            {
                // Capture the current ingredient in a local variable for the closure
                string currentIngredient = ingredient;
                itemButton.onClick.AddListener(() => OnIngredientTapped(currentIngredient));
            }
        }
    }

    IEnumerator FetchRecipeData()
    {
        using (UnityWebRequest www = UnityWebRequest.Get(apiBaseUrl + "/recipe"))
        {
            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                FullRecipe recipe = JsonUtility.FromJson<FullRecipe>(www.downloadHandler.text);
                PopulateIngredientList(recipe.ingredients);
            }
            else
            {
                Debug.LogError("Error fetching recipe data: " + www.error);
            }
        }
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

[System.Serializable]
public class FullRecipe
{
    public string[] ingredients;
}

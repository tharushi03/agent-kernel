class RecommendationAgent:
    """
    Recommendation Agent - Ranks vehicles and provides explanations.
    Generates clear, actionable recommendations.
    """

    def rank(self, results):
        """
        Take search results and produce final recommendations.
        Returns formatted recommendations.
        """
        if not results:
            return "😅 No exact matches found. Try adjusting your preferences!"

        output = "\n🚗 Top Recommendations:\n\n"

        for i, result in enumerate(results[:3], 1):
            vehicle = result['vehicle']
            output += f"{i}. {vehicle['make']} {vehicle['model']} ({vehicle['year']})\n"
            output += f"   💰 Price: ${vehicle['price']:,}\n"
            output += f"   ⛽ MPG: {vehicle['mpg']}\n"
            output += f"   🛡️ Safety: {vehicle['safety_rating']}/5\n"
            output += f"   📝 {vehicle['description']}\n"
            output += f"   ✅ {', '.join(result['matches'])}\n"
            output += "\n"

        output += "💡 Type 'history' to see past searches\n"
        output += "💡 Type 'show preferences' to see saved preferences\n"
        output += "💡 Type 'exit' to quit (your preferences are saved!)\n"

        return output

# run_ww.py

from entity_extraction import (
    process_texts_to_entities_and_triplets,
    write_to_database,
    list_entities_and_relationships,
    close_driver
)



def main():
    # List of different corpus texts
    corpora = [
        """As the sun dips beneath the horizon, the once vibrant city of Mordale transforms into a haunting silhouette against the blood-red sky. The streets, once bustling with merchants and minstrels, now echo with eerie silence. You, Dustin the Barbarian, stand in the shadow of the grand cathedral, a relic from your time as an acolyte. You feel the cold stone beneath your calloused fingers and the chill of the evening wind raising goosebumps on your skin.

From the corner of your eye, you spot a hooded figure darting into an alleyway. It's Father Eldrige, the elderly priest who was like a father to you during your acolyte days. He seems anxious, glancing over his shoulder as if pursued by unseen forces. He locks eyes with you, a flash of recognition and fear in his gaze.

Options:

1. Approach Father Eldrige to find out why he's acting so strangely.

2. Follow him quietly from a distance to see where he's headed.

3. Return to the cathedral to investigate if anything has been disturbed.

4. Seek out the city guards and report Eldrige's suspicious behavior.

5. Ignore the incident and head to the nearest tavern for a drink, deciding to deal with it in the morning.""",

"""
You swiftly move through the shadowed streets, your footfalls muffled by the evening's quiet. As you approach Father Eldrige, he jumps, clearly startled. His eyes, wide with fear, soften as he recognizes you. 'Dustin,' he breathes, a sigh of relief escaping his lips. 'I didn't expect to see you here.'

His hands tremble as he pulls a small, metallic object from his robe, an ancient relic you recognize from your acolyte days. It's a sacred artifact, said to hold immense power, and it's missing from the cathedral's vault.

'I found this in my quarters, Dustin. Someone is trying to frame me,' Father Eldrige confesses, his voice barely a whisper.

Options:

1. Offer to hide the artifact for Father Eldrige while you investigate the matter.

2. Suggest returning the artifact to the cathedral's vault secretly and hope the culprit returns to the scene.

3. Encourage Father Eldrige to turn himself and the artifact in to the city guards, explaining the situation.

4. Take the artifact and confront the cathedral's high priest, accusing him of the conspiracy.

5. Leave Father Eldrige to deal with the situation on his own, choosing to distance yourself from the unfolding scandal."""

        ,
        # Add more corpus texts as needed
    ]

    # Process texts to extract entities and triplets
    entity_dict, standardized_triplets = process_texts_to_entities_and_triplets(corpora)
    # Write the extracted data to Neo4j
    write_to_database(entity_dict, standardized_triplets)
    
    # Optionally, list all entities and relationships
    #list_entities_and_relationships()
    
    # Close the Neo4j driver connection
    close_driver()

if __name__ == "__main__":
    main()


import os
import requests # For Ollama API

if __name__ == "__main__":

    ### Initial Error Checking ####################################################################

    # If Agents and Memory directories do not exist (first run),
    # Then create the Agents and Memory directory with default files and store default values in Agents dict and long term memory,
    # Else load existing .md files into Agents dict and long term memory.
    agents = {}
    lt_memory = ""
    if os.listdir("Agents") == []:
        os.mkdir("Agents")
        agents["Default_Jimmy"] = "You are a helpful assistant named Jimmy."
        os.close(os.open("Agents/Agent_01.md", "x").write(agents["Default_Jimmy"]))
    else:
        for x in os.listdir("Agents"):
            agents[x[:-3]] = open("Agents/" + x, "r").read()

    if os.listdir("Memory") == []:
        os.mkdir("Memory")
        lt_memory = ""
        # TODO: If you never add any default system prompt, remove the .write() from below
        os.close(os.open("Memory/System.md", "x").write(lt_memory))
    else:
        lt_memory = open("Memory/System.md", "r").read()
    

    ### Super Loop ################################################################################
    
    user_query = ""
    while True:
        user_query = input("Query:  ")
        if user_query == "/quit" or user_query == "/exit":
            break

        
        # TODO: implement seperate agent personality logic
        payload = lt_memory + " " + agents["Muninn"] + " " + user_query

        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "gemma3:1b",
            "prompt": payload,
            "stream": False
            })
        print(response.json()["response"])

    
    ### Mop Up ####################################################################################
    print("Till we meet again.")
        

    
import bot

if __name__ == '__main__':
    config = {}
    with open('./config/config.txt') as f:
        lines = f.readlines()
        for line in lines:
            if(line.startswith("#")):
                continue
 
            var_name, value = line.split('=')
   
            if value.startswith("empty"):
                print("ERROR: no valid API key found for "+var_name)
                exit(1)
            #else    
            config[var_name.strip()]=value.strip()
 
    bot.switch_on_bot(config)

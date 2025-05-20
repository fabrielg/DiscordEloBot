import discord

async def change_user_name(member, name):
    try:
        # Define a custom nickname for new members

        # Change the member's nickname
        await member.edit(nick=name)
        print(f"Changed nickname for {member.name} to {name}")
        
    except discord.Forbidden:
        print("I don't have permission to change that user's nickname.")
    except discord.HTTPException as e:
        print(f"Failed to change nickname: {e}")

from srcs.bot import *
from srcs.db import *
from srcs.elo import *
from srcs.match import *
from srcs.utils import *
from srcs.member import *
from srcs.commands import *
from srcs.fake import fake_db
#reset the db:
# Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# fake_db()

bot.run(os.getenv('TOKEN'))


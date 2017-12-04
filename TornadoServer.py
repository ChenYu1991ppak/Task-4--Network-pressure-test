import os

import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.gen

import motor

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)

mongo_server = "192.168.80.131"
mongo_port = 27017
database = "BookStore"
collection1 = "users"
collection2 = "books"

class Visithander(tornado.web.RequestHandler):
    def get(self):
        self.render(
            'login.html',
            page_title="User Login",
        )

class Indexhander(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        # Classify the user's account
        user = self.get_argument("user")
        passwd = self.get_argument("passwd")
        is_exist = yield self.application.db[collection1].find({"user": user, "passwd": passwd}).fetch_next
        if is_exist:
            books = yield self.application.db[collection2].find().to_list(length=100)
            self.render(
                "index.html",
                page_title="Recommended Reading",
                books=books
            )
        else:
            self.redirect("/")

class Registerhander(tornado.web.RequestHandler):
    def post(self):
        self.render(
            "register.html",
            page_title="User register",
        )

class RegisterReturnhander(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        user = self.get_argument("user")
        passwd = self.get_argument("passwd")
        self.application.db[collection1].insert({"user": user, "passwd": passwd})
        self.redirect("/")

class Detailhander(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, id=None):
        result = yield self.application.db[collection2].find({"id": id}).to_list(length=1)
        self.render(
            "detail.html",
            page_title="Book Detail",
            book=result[0]
        )

class BookModule(tornado.web.UIModule):
    def render(self, book):
        return self.render_string('modules/book.html', book=book)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', Visithander),
            (r'/index', Indexhander),
            (r'/register', Registerhander),
            (r'/return', RegisterReturnhander),
            (r'/detail/([0-9Xx\-]+)', Detailhander)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            ui_modules={'Book': BookModule}
        )
        self.db = motor.MotorClient(mongo_server)[database]
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    app = Application()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

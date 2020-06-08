from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from flask_graphql import GraphQLView
#################################
app = Flask(__name__)
app.debug = True

basedir = os.path.abspath(os.path.dirname(__file__))
# Configs
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'testgraph.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# Modules
db = SQLAlchemy(app)

# Models
'''
Como arrancar el modelo
$ python
>>> from app import db, User, Post
>>> db.create_all()
>>> john = User(username='johndoe')
>>> post = Post()
>>> post.title = "Hello World"
>>> post.body = "This is the first post"
>>> post.author = john
>>> db.session.add(post)
>>> db.session.add(john)
>>> db.session.commit()
>>> User.query.all()
[<User 'johndoe'>]
>>> Post.query.all()
[<Post 'Hello World'>
'''
class User(db.Model):
    __tablename__ = 'users'
    uuid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), index=True, unique=True)
    posts = db.relationship('Post', backref='author')
    
    def __repr__(self):
        return '<User %r>' % self.username


class Post(db.Model):
    __tablename__ = 'posts'
    uuid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), index=True)
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.uuid'))
    def __repr__(self):
        return '<Post %r>' % self.title


# Schema Objects
class PostObject(SQLAlchemyObjectType):

    class Meta:
        model = Post
        interfaces = (graphene.relay.Node, )


class UserObject(SQLAlchemyObjectType):

   class Meta:
       model = User
       interfaces = (graphene.relay.Node, )


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_posts = SQLAlchemyConnectionField(PostObject)
    all_users = SQLAlchemyConnectionField(UserObject)

class CreatePost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        body = graphene.String(required=True) 
        username = graphene.String(required=True)
    post = graphene.Field(lambda: PostObject)

    def mutate(self, info, title, body, username):
        user = User.query.filter_by(username=username).first()
        post = Post(title=title, body=body)
        if user is not None:
            post.author = user
        db.session.add(post)
        db.session.commit()
        return CreatePost(post=post)


class Mutation(graphene.ObjectType):
    create_post = CreatePost.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
#### views
@app.route('/')
def index():
    return '<p> Hello World!</p>'


app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True # for having the GraphiQL interface
    )
)

##################################
if __name__ == '__main__':
     app.run(host='0.0.0.0')
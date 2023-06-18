import os
import random

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, jsonify
from flask_login import login_required, current_user

import openai
from python_graphql_client import GraphqlClient


from src import db
from src.accounts.models import User, Biome, Scene, Comment, Vote
from src.accounts.forms import BiomeForm, SceneForm, SceneEditForm


core_bp = Blueprint("core", __name__)
openai.api_key = os.environ['OPENAI_API_KEY']
client = GraphqlClient(endpoint='https://www.dnd5eapi.co/graphql')

# NOT AUTH REQUIRED

@core_bp.route("/")
def home():
    try:
        shared_scenes = Scene.query.filter_by(shared=True).all()
        return render_template("core/index.html", shared_scenes=shared_scenes)
    except:
        return render_template("core/index.html")



# AUTH REQUIRED

######################################################################### BIOMES

@core_bp.route("/biomes")
@login_required
def biomes():
    if current_user.is_authenticated:
        user = current_user
        biomes = Biome.query.filter_by(user_id=current_user.id).all()
        shared_scenes = Scene.query.filter_by(shared=True).all()
        return render_template('core/biomes.html', biomes=biomes, shared_scenes=shared_scenes, user=user)
    
@core_bp.route("/biomes/new", methods=["GET", "POST"])
@login_required
def create_biome():
    form = BiomeForm()
    if form.validate_on_submit():
        biome = Biome(name=form.name.data, description=form.description.data, user_id=current_user.id)
        db.session.add(biome)
        db.session.commit()
        flash("New biome created!", "success")
        return redirect(url_for("core.biomes"))
    return render_template("core/create_biome.html", form=form)

@core_bp.route("/biomes/<int:biome_id>/edit", methods=["GET", "POST"])
@login_required
def edit_biome(biome_id):
    biome = Biome.query.get_or_404(biome_id)
    if biome.user_id != current_user.id:
        abort(403)
    form = BiomeForm(obj=biome)
    if form.validate_on_submit():
        biome.name = form.name.data
        biome.description = form.description.data
        db.session.commit()
        flash("Biome updated!", "success")
        return redirect(url_for("core.biomes"))
    return render_template("core/edit_biome.html", form=form, biome=biome)

@core_bp.route("/biomes/<int:biome_id>/delete", methods=["POST"])
@login_required
def delete_biome(biome_id):
    biome = Biome.query.get_or_404(biome_id)
    if biome.user_id != current_user.id:
        abort(403)
    db.session.delete(biome)
    db.session.commit()
    flash("Biome deleted!", "success")
    return redirect(url_for("core.biomes"))

######################################################################### SCENES
@core_bp.route('/biome/<int:biome_id>/scenes')
def scenes(biome_id):
    biome = Biome.query.get_or_404(biome_id)
    scenes = Scene.query.filter_by(biome_id=biome_id).all()
    return render_template("core/scenes.html", biome=biome, scenes=scenes)
    

@core_bp.route('/biome/<int:biome_id>/scenes/create', methods=['GET', 'POST'])
def create_scene(biome_id):
    form = SceneForm()
    biome = Biome.query.get_or_404(biome_id)

    if form.validate_on_submit():
        scene = Scene(focus=form.focus.data, vibe=form.vibe.data, biome_id=biome_id)
        db.session.add(scene)
        scene.generate_description(biome)
        db.session.commit()
        flash('Scene created successfully!', 'success')
        return redirect(url_for('core.scenes', biome_id=biome_id, biome=biome))
    else:
        flash(form.errors)

    return render_template('core/create_scene.html', form=form, biome_id=biome_id, biome=biome)

@core_bp.route('/add_to_biome/<int:scene_id>', methods=['POST'])
@login_required
def add_to_biome(scene_id):
    selected_biome_id = request.form.get('biome_id')
    selected_biome = Biome.query.get(selected_biome_id)
    shared_scene = Scene.query.get(scene_id)

    # Create a new scene for user
    new_scene = Scene(
        focus=shared_scene.focus,
        vibe=shared_scene.vibe,
        biome_id=selected_biome_id
    )

    db.session.add(new_scene)
    new_scene.generate_description(selected_biome)
    db.session.commit()

    flash('Scene added to biome successfully', 'success')
    return redirect(url_for('core.biomes'))

@core_bp.route('/biome/<int:biome_id>/scenes/<int:scene_id>/edit', methods=['GET', 'POST'])
def edit_scene(biome_id, scene_id):
    scene = Scene.query.get_or_404(scene_id)
    form = SceneEditForm(obj=scene)
    biome = Biome.query.get_or_404(biome_id)

    if form.validate_on_submit():
        form.populate_obj(scene)
        db.session.commit()
        flash('Scene updated successfully!', 'success')
        return redirect(url_for('core.scenes', biome_id=biome_id, biome=biome))

    return render_template('core/edit_scene.html', form=form, biome_id=biome.id, scene=scene, biome=biome)

@core_bp.route("/biomes/<int:biome_id>/scenes/<int:scene_id>/delete", methods=['POST'])
@login_required
def delete_scene(biome_id, scene_id):
    biome = Biome.query.get_or_404(biome_id)
    scene = Scene.query.get_or_404(scene_id)
    if biome.user_id!= current_user.id:
        abort(403)
    db.session.delete(scene)
    db.session.commit()
    flash("Scene deleted!", "success")
    return redirect(url_for("core.scenes", biome_id=biome_id))

@core_bp.route("/biome/<biome_id>/scene/<scene_id>/share", methods=["POST"])
def share_scene(biome_id, scene_id):
    scene = Scene.query.get_or_404(scene_id)
    scene.shared = True
    db.session.commit()
    flash('Scene shared successfully.', 'success')
    return redirect(url_for('core.biomes', biome_id=biome_id))


#######################################################################Encounter

@core_bp.route("/encounter/<int:biome_id>")
@login_required
def encounter(biome_id, scene_id=None):
    if scene_id is not None:
        scene = Scene.query.get_or_404(scene_id)
    else:
        scenes = Scene.query.filter_by(biome_id=biome_id).all()
        scene = random.choice(scenes)

    response = openai.Image.create(
        prompt=f"A magic realism illustration, 4k, detailed, trending in artstation, fantasY2k | {scene.image_text}",
        n=1,
        size="512x512"
    )
    img_url = response['data'][0]['url']

    return render_template("core/encounter.html", scene=scene, img_url=img_url)



@core_bp.route('/encounter/random')
def generate_random_encounter():
    biomes = Biome.query.all()
    biome = random.choice(biomes)
    return redirect(url_for('core.encounter', biome_id=biome.id))

################################################################ Interacting with Shared Scenes

@core_bp.route('/vote_scene/<int:scene_id>/<string:vote_type>', methods=['POST'])
@login_required
def vote_scene(scene_id, vote_type):
    scene = Scene.query.get(scene_id)

    if scene is None:
        return redirect(url_for('core.biomes'))

    vote = Vote.query.filter_by(user_id=current_user.id, scene_id=scene_id).first()

    if vote is None:
        vote = Vote(user_id=current_user.id, scene_id=scene_id)
        db.session.add(vote)
    else:
        vote.is_upvote = (vote_type == 'upvote')

    db.session.commit()

    scene_avg_vote = scene.avg_vote if scene.avg_vote is not None else 0

    return jsonify({'avg_vote': scene_avg_vote})


@core_bp.route('/add_comment.<int:scene_id>', methods=['POST'])
@login_required
def add_comment(scene_id):
    scene = Scene.query.get(scene_id)

    if scene is None:
        return redirect(url_for('core.biomes'))
    
    comment_text = request.form.get('comment')

    comment = Comment(user_id=current_user.id, scene_id=scene_id, text=comment_text)
    db.session.add(comment)
    db.session.commit()
    scene.update_comment_count()

    return redirect(url_for('core.view_comments', scene_id=scene.id))

@core_bp.route('/view_comments/<int:scene_id>')
def view_comments(scene_id):
    scene = Scene.query.get(scene_id)

    if scene is None:
        return render_template('core.biomes', error_message='scene not found')
    
    comments = Comment.query.filter_by(scene_id=scene_id).all()

    return render_template('core/view_comments.html', scene=scene, comments=comments)

@core_bp.route('/delete_comment/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)

    # Check if the comment exists
    if comment is None:
        return jsonify(message='Comment not found'), 404

    # Check if the current user is the owner of the comment
    if comment.user != current_user:
        return jsonify(message='Unauthorized'), 403

    # Delete the comment
    db.session.delete(comment)
    db.session.commit()

    return jsonify(message='Comment deleted')

@core_bp.route('/update_comment/<comment_id>', methods=['PATCH'])
def update_comment(comment_id):
    updated_comment_text = request.json.get('commentText')

    comment = Comment.query.get(comment_id)
    comment.text = updated_comment_text

    db.session.add(comment)
    db.session.commit()

    return jsonify(message='Comment updated')



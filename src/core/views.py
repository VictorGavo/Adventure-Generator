import os
import random

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

import openai
from python_graphql_client import GraphqlClient


from src import db
from src.accounts.models import User, Biome, Scene
from src.accounts.forms import BiomeForm, SceneForm, SceneEditForm


core_bp = Blueprint("core", __name__)
openai.api_key = os.environ['OPENAI_API_KEY']
client = GraphqlClient(endpoint='https://www.dnd5eapi.co/graphql')

# NOT AUTH REQUIRED

@core_bp.route("/")
@login_required
def home():
    return render_template("core/index.html")



# AUTH REQUIRED

######################################################################### BIOMES

@core_bp.route("/biomes")
@login_required
def biomes():
    if current_user.is_authenticated:
        biomes = Biome.query.filter_by(user_id=current_user.id).all()
        return render_template('core/biomes.html', biomes=biomes)
    
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
        prompt=f"A digital illustration, 4k, detailed, trending in artstation, fantasy | {scene.image_text}",
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


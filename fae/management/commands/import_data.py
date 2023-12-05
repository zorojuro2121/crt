import csv
import os
from django.core.files import File
from django.core.management.base import BaseCommand
from fae.models import Technologies  # Import your City model or relevant models
class Command(BaseCommand):
    help = 'Import data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        with open(file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                obj = Technologies()
                # Extract data from the CSV row

                obj.application_name = row['application_name']
                obj.block_names = row['block_names']

                image_path = row['myimg']
                image_file_path = os.path.join(os.getcwd(), image_path)
                with open(image_file_path, 'rb') as image_file:
                    obj.myimg.save(os.path.basename(image_path), File(image_file))
                # ...

                # Create an instance of your model and save it to the database
                # fae = Technologies(block_names=block_names)
                # fae.save()
                obj.save()

        self.stdout.write(self.style.SUCCESS('Data import successful.'))

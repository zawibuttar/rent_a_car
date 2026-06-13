from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, CustomerProfile, OwnerProfile, SocialMediaLink, HeroBanner

ALLOWED_REGISTER_ROLES = {User.Role.CUSTOMER, User.Role.OWNER}


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password2', 'role']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate_role(self, value):
        if value not in ALLOWED_REGISTER_ROLES:
            raise serializers.ValidationError(
                "Invalid role. Registration is only allowed as customer or owner."
            )
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        validate_password(password, user=User(
            username=attrs.get('username', ''),
            email=attrs.get('email', ''),
        ))
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2') 

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role']
        )
        if user.role == User.Role.CUSTOMER:
            CustomerProfile.objects.create(user=user)
        elif user.role == User.Role.OWNER:
            OwnerProfile.objects.create(user=user)

        return user
    
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        data['user'] = user
        return data
    



class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'display_name', 'email', 'role',
            'is_superuser', 'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'is_superuser', 'is_active', 'date_joined']

    def get_display_name(self, obj):
        from rentacar.utils import format_display_name
        return format_display_name(obj.username)


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ['id', 'user', 'profile_picture', 'phone_number', 'national_id_number', 'driving_license_number', 'address', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class OwnerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OwnerProfile
        fields = ['id', 'user', 'profile_picture', 'phone_number', 'national_id_number', 'address', 'is_verified', 'total_earnings', 'created_at']
        read_only_fields = ['id', 'user', 'is_verified', 'total_earnings', 'created_at']




class SocialMediaLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMediaLink
        fields = ['id', 'platform_name', 'url', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_platform_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Platform name is required.')
        return value

    def validate_url(self, value):
        value = (value or '').strip()
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError('URL must start with http:// or https://')
        return value


class HeroBannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    orientation_label = serializers.SerializerMethodField()

    class Meta:
        model = HeroBanner
        fields = [
            'id', 'title', 'image', 'image_url', 'width', 'height',
            'orientation_label', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'width', 'height', 'created_at', 'image_url', 'orientation_label']

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_orientation_label(self, obj):
        if obj.width and obj.height:
            return f'{obj.width}×{obj.height} landscape'
        return 'Landscape'

    def validate_image(self, image_file):
        from rentacar.image_validation import validate_hero_banner_image

        if not image_file and self.instance:
            return image_file
        err = validate_hero_banner_image(image_file)
        if err:
            raise serializers.ValidationError(err)
        return image_file

    def validate(self, attrs):
        if not self.instance and not attrs.get('image'):
            raise serializers.ValidationError({'image': 'Image file is required.'})
        return attrs

    def create(self, validated_data):
        image_file = validated_data.get('image')
        if image_file:
            from rentacar.image_validation import read_image_dimensions

            width, height = read_image_dimensions(image_file)
            validated_data['width'] = width
            validated_data['height'] = height
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = validated_data.get('image')
        if image_file:
            from rentacar.image_validation import read_image_dimensions

            width, height = read_image_dimensions(image_file)
            validated_data['width'] = width
            validated_data['height'] = height
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, value):
        if value['new_password'] != value['new_password2']:
            raise serializers.ValidationError("New passwords do not match.")
        return value